#!/usr/bin/env python3
"""
Test Configuration Management System
Validates API credential testing, methodology tuning, and configuration validation
"""

import unittest
import tempfile
import os
import sys
import yaml
import json
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.config_manager import (
    ConfigurationManager, 
    APICredentials, 
    MethodologyConfig, 
    SystemConfig,
    APIStatus,
    test_all_apis
)


class TestConfigurationManager(unittest.TestCase):
    """Test configuration management functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_config_path = os.path.join(self.test_dir, "test_config.yaml")
        
        # Create configuration manager
        self.config_manager = ConfigurationManager(self.test_config_path)
    
    def tearDown(self):
        """Clean up test resources"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_configuration_initialization(self):
        """Test configuration manager initialization"""
        
        # Should create default configuration
        self.assertIsNotNone(self.config_manager.methodology_config)
        self.assertIsNotNone(self.config_manager.system_config)
        self.assertGreater(len(self.config_manager.api_credentials), 0)
        
        # Check that config file was created
        self.assertTrue(os.path.exists(self.test_config_path))
        
        # Check methodology config structure
        method_config = self.config_manager.methodology_config
        self.assertIn('fundamental', method_config.component_weights)
        self.assertIn('quality', method_config.component_weights)
        self.assertIn('growth', method_config.component_weights)
        self.assertIn('sentiment', method_config.component_weights)
        
        # Weights should sum to 1.0
        total_weight = sum(method_config.component_weights.values())
        self.assertAlmostEqual(total_weight, 1.0, places=2)
    
    def test_api_credentials_management(self):
        """Test API credentials management"""
        
        # Test updating credentials
        test_credentials = {
            'client_id': 'test_client_id',
            'client_secret': 'test_secret',
            'user_agent': 'test_agent'
        }
        
        success = self.config_manager.update_api_credentials('reddit', test_credentials)
        self.assertTrue(success)
        
        # Check that credentials were stored
        reddit_cred = self.config_manager.api_credentials['reddit']
        self.assertEqual(reddit_cred.credentials['client_id'], 'test_client_id')
        self.assertEqual(reddit_cred.credentials['client_secret'], 'test_secret')
        self.assertEqual(reddit_cred.credentials['user_agent'], 'test_agent')
        
        # Test configuration save/load cycle
        self.config_manager.save_configuration()
        
        # Create new config manager and load
        new_config_manager = ConfigurationManager(self.test_config_path)
        new_reddit_cred = new_config_manager.api_credentials['reddit']
        
        self.assertEqual(new_reddit_cred.credentials['client_id'], 'test_client_id')
    
    @patch('yfinance.Ticker')
    def test_yahoo_finance_api_testing(self, mock_ticker):
        """Test Yahoo Finance API testing"""
        
        # Mock successful response
        mock_ticker_instance = MagicMock()
        mock_ticker_instance.info = {'symbol': 'AAPL', 'shortName': 'Apple Inc.'}
        mock_ticker.return_value = mock_ticker_instance
        
        status, message = self.config_manager.test_api_credentials('yahoo_finance')
        
        self.assertEqual(status, APIStatus.HEALTHY)
        self.assertIn('Successfully', message)
        
        # Test with failure
        mock_ticker_instance.info = {}
        status, message = self.config_manager.test_api_credentials('yahoo_finance')
        self.assertEqual(status, APIStatus.LIMITED)
    
    @patch('praw.Reddit')
    def test_reddit_api_testing(self, mock_reddit):
        """Test Reddit API testing"""
        
        # Set up credentials first
        test_credentials = {
            'client_id': 'test_client_id',
            'client_secret': 'test_secret',
            'user_agent': 'test_agent'
        }
        self.config_manager.update_api_credentials('reddit', test_credentials)
        
        # Mock successful response
        mock_reddit_instance = MagicMock()
        mock_subreddit = MagicMock()
        mock_subreddit.hot.return_value = [{'title': 'Test Post'}]
        mock_reddit_instance.subreddit.return_value = mock_subreddit
        mock_reddit.return_value = mock_reddit_instance
        
        status, message = self.config_manager.test_api_credentials('reddit')
        
        self.assertEqual(status, APIStatus.HEALTHY)
        self.assertIn('Successfully', message)
        
        # Test with no credentials
        self.config_manager.api_credentials['reddit'].credentials = {}
        status, message = self.config_manager.test_api_credentials('reddit')
        self.assertEqual(status, APIStatus.INVALID_CREDENTIALS)
    
    @patch('requests.get')
    def test_alpha_vantage_api_testing(self, mock_get):
        """Test Alpha Vantage API testing"""
        
        # Set up credentials
        test_credentials = {'api_key': 'test_api_key'}
        self.config_manager.update_api_credentials('alpha_vantage', test_credentials)
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'Global Quote': {
                '01. symbol': 'AAPL',
                '05. price': '150.00'
            }
        }
        mock_get.return_value = mock_response
        
        status, message = self.config_manager.test_api_credentials('alpha_vantage')
        
        self.assertEqual(status, APIStatus.HEALTHY)
        self.assertIn('Successfully', message)
        
        # Test with error response
        mock_response.json.return_value = {'Error Message': 'Invalid API call'}
        status, message = self.config_manager.test_api_credentials('alpha_vantage')
        self.assertEqual(status, APIStatus.INVALID_CREDENTIALS)
        
        # Test with rate limit
        mock_response.json.return_value = {'Note': 'Thank you for using Alpha Vantage! Our standard API call frequency is 5 calls per minute'}
        status, message = self.config_manager.test_api_credentials('alpha_vantage')
        self.assertEqual(status, APIStatus.RATE_LIMITED)
    
    def test_methodology_configuration_validation(self):
        """Test methodology configuration validation"""
        
        # Test valid configuration
        is_valid, errors = self.config_manager.validate_methodology_config()
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
        # Test invalid weight sum
        self.config_manager.methodology_config.component_weights['fundamental'] = 0.5
        is_valid, errors = self.config_manager.validate_methodology_config()
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any('sum to 1.0' in error for error in errors))
        
        # Test invalid quality threshold
        self.config_manager.methodology_config.component_weights['fundamental'] = 0.4  # Reset
        self.config_manager.methodology_config.quality_thresholds['minimum_data_quality'] = 1.5
        is_valid, errors = self.config_manager.validate_methodology_config()
        self.assertFalse(is_valid)
        self.assertTrue(any('0-1' in error for error in errors))
        
        # Test invalid staleness limit
        self.config_manager.methodology_config.quality_thresholds['minimum_data_quality'] = 0.6  # Reset
        self.config_manager.methodology_config.staleness_limits['fundamentals_days'] = 400
        is_valid, errors = self.config_manager.validate_methodology_config()
        self.assertFalse(is_valid)
        self.assertTrue(any('1-365 days' in error for error in errors))
    
    def test_methodology_configuration_updates(self):
        """Test methodology configuration updates"""
        
        # Test valid update
        updates = {
            'component_weights': {
                'fundamental': 0.45,
                'quality': 0.25,
                'growth': 0.20,
                'sentiment': 0.10
            },
            'quality_thresholds': {
                'minimum_data_quality': 0.7,
                'high_quality_threshold': 0.85,
                'excellent_quality_threshold': 0.95
            }
        }
        
        success, errors = self.config_manager.update_methodology_config(updates)
        self.assertTrue(success)
        self.assertEqual(len(errors), 0)
        
        # Verify updates were applied
        self.assertAlmostEqual(
            self.config_manager.methodology_config.component_weights['fundamental'],
            0.45, places=2
        )
        self.assertAlmostEqual(
            self.config_manager.methodology_config.quality_thresholds['minimum_data_quality'],
            0.7, places=2
        )
        
        # Test invalid update
        invalid_updates = {
            'component_weights': {
                'fundamental': 0.6,  # Too high, won't sum to 1.0
                'quality': 0.25,
                'growth': 0.20,
                'sentiment': 0.10
            }
        }
        
        success, errors = self.config_manager.update_methodology_config(invalid_updates)
        self.assertFalse(success)
        self.assertGreater(len(errors), 0)
    
    def test_api_status_summary(self):
        """Test API status summary generation"""
        
        summary = self.config_manager.get_api_status_summary()
        
        self.assertIsInstance(summary, dict)
        self.assertGreater(len(summary), 0)
        
        # Check required fields for each API
        for api_name, info in summary.items():
            self.assertIn('description', info)
            self.assertIn('status', info)
            self.assertIn('has_credentials', info)
            self.assertIn('required_fields', info)
            self.assertIn('configured_fields', info)
            
            # Check that status is a valid value
            valid_statuses = [status.value for status in APIStatus]
            self.assertIn(info['status'], valid_statuses)
    
    def test_configuration_health_check(self):
        """Test configuration health check"""
        
        health = self.config_manager.get_configuration_health()
        
        self.assertIsInstance(health, dict)
        self.assertIn('overall_status', health)
        self.assertIn('issues', health)
        self.assertIn('api_summary', health)
        self.assertIn('methodology_valid', health)
        self.assertIn('last_check', health)
        self.assertIn('api_health_percentage', health)
        
        # Should be healthy with default config
        self.assertIn(health['overall_status'], ['healthy', 'warning'])  # Warning is OK due to untested APIs
        self.assertTrue(health['methodology_valid'])
        
        # Health percentage should be 0-100
        self.assertGreaterEqual(health['api_health_percentage'], 0)
        self.assertLessEqual(health['api_health_percentage'], 100)
    
    def test_configuration_export_import(self):
        """Test configuration export functionality"""
        
        # Set up some test data
        test_credentials = {'api_key': 'test_key'}
        self.config_manager.update_api_credentials('alpha_vantage', test_credentials)
        
        # Export configuration
        export_path = os.path.join(self.test_dir, "test_export.json")
        success = self.config_manager.export_configuration(export_path)
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(export_path))
        
        # Check export content
        with open(export_path, 'r') as f:
            export_data = json.load(f)
        
        self.assertIn('api_credentials', export_data)
        self.assertIn('methodology', export_data)
        self.assertIn('system', export_data)
        self.assertIn('export_timestamp', export_data)
        
        # Should not contain sensitive credentials
        alpha_vantage_info = export_data['api_credentials']['alpha_vantage']
        self.assertNotIn('credentials', alpha_vantage_info)
        self.assertTrue(alpha_vantage_info['has_credentials'])
    
    def test_configuration_save_load_cycle(self):
        """Test complete configuration save/load cycle"""
        
        # Modify configuration
        self.config_manager.methodology_config.component_weights['fundamental'] = 0.35
        self.config_manager.methodology_config.component_weights['quality'] = 0.30
        self.config_manager.methodology_config.quality_thresholds['minimum_data_quality'] = 0.75
        
        test_credentials = {
            'client_id': 'test_id',
            'client_secret': 'test_secret',
            'user_agent': 'test_user_agent'
        }
        self.config_manager.update_api_credentials('reddit', test_credentials)
        
        # Save configuration
        success = self.config_manager.save_configuration()
        self.assertTrue(success)
        
        # Create new manager and load
        new_manager = ConfigurationManager(self.test_config_path)
        
        # Verify configuration was loaded correctly
        self.assertAlmostEqual(
            new_manager.methodology_config.component_weights['fundamental'],
            0.35, places=2
        )
        self.assertAlmostEqual(
            new_manager.methodology_config.component_weights['quality'],
            0.30, places=2
        )
        self.assertAlmostEqual(
            new_manager.methodology_config.quality_thresholds['minimum_data_quality'],
            0.75, places=2
        )
        
        # Verify API credentials were loaded
        reddit_cred = new_manager.api_credentials['reddit']
        self.assertEqual(reddit_cred.credentials['client_id'], 'test_id')
        self.assertEqual(reddit_cred.credentials['client_secret'], 'test_secret')
    
    def test_test_all_apis_function(self):
        """Test the test_all_apis convenience function"""
        
        # Mock the test methods to avoid actual API calls
        with patch.object(self.config_manager, 'test_api_credentials') as mock_test:
            mock_test.return_value = (APIStatus.HEALTHY, "Test successful")
            
            results = test_all_apis(self.config_manager)
            
            self.assertIsInstance(results, dict)
            self.assertGreater(len(results), 0)
            
            # Check that all results have the expected format
            for api_name, (status, message) in results.items():
                self.assertIsInstance(status, APIStatus)
                self.assertIsInstance(message, str)
                
                # Check that the credential status was updated
                self.assertEqual(self.config_manager.api_credentials[api_name].status, APIStatus.HEALTHY)
                self.assertIsNotNone(self.config_manager.api_credentials[api_name].last_tested)
    
    def test_error_handling(self):
        """Test error handling in configuration management"""
        
        # Test with invalid config path
        invalid_path = "/invalid/path/config.yaml"
        invalid_manager = ConfigurationManager(invalid_path)
        
        # Should still create a working manager with defaults
        self.assertIsNotNone(invalid_manager.methodology_config)
        
        # Test saving to invalid path should fail gracefully
        success = invalid_manager.save_configuration()
        self.assertFalse(success)
        
        # Test export to invalid path should fail gracefully
        success = invalid_manager.export_configuration("/invalid/export/path.json")
        self.assertFalse(success)
        
        # Test API testing with unknown API
        status, message = self.config_manager.test_api_credentials('unknown_api')
        self.assertEqual(status, APIStatus.FAILED)
        self.assertIn('Unknown API', message)
    
    def test_api_templates(self):
        """Test API templates initialization"""
        
        templates = self.config_manager.api_templates
        
        self.assertIn('yahoo_finance', templates)
        self.assertIn('reddit', templates)
        self.assertIn('alpha_vantage', templates)
        self.assertIn('news_api', templates)
        
        # Check template structure
        for api_name, template in templates.items():
            self.assertIn('description', template)
            self.assertIn('required_fields', template)
            self.assertIn('optional_fields', template)
            self.assertIn('test_endpoint', template)
            self.assertIn('rate_limits', template)
            
            # Required fields should be a list
            self.assertIsInstance(template['required_fields'], list)
            self.assertIsInstance(template['optional_fields'], list)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)