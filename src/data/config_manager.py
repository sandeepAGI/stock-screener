#!/usr/bin/env python3
"""
Live Configuration Management System
Provides API credential testing, methodology tuning, and configuration validation
"""

import os
import yaml
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import yfinance as yf
import praw
from enum import Enum

logger = logging.getLogger(__name__)


class APIStatus(Enum):
    """API connection status"""
    HEALTHY = "healthy"
    LIMITED = "limited"
    FAILED = "failed"
    UNTESTED = "untested"
    INVALID_CREDENTIALS = "invalid_credentials"
    RATE_LIMITED = "rate_limited"


@dataclass
class APICredentials:
    """API credentials container"""
    api_name: str
    credentials: Dict[str, str]
    status: APIStatus
    last_tested: Optional[datetime]
    test_result: Optional[str]
    rate_limit_info: Dict[str, Any]


@dataclass
class MethodologyConfig:
    """Methodology configuration container"""
    component_weights: Dict[str, float]
    scoring_thresholds: Dict[str, Dict[str, float]]
    quality_thresholds: Dict[str, float]
    staleness_limits: Dict[str, int]
    sector_adjustments: Dict[str, Dict[str, float]]


@dataclass
class SystemConfig:
    """System configuration container"""
    database_path: str
    logging_level: str
    cache_settings: Dict[str, Any]
    performance_settings: Dict[str, Any]
    backup_settings: Dict[str, Any]


class ConfigurationManager:
    """Manages live configuration, API credentials, and methodology settings"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/config.yaml"
        self.config_dir = Path(self.config_path).parent
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize configuration
        self.api_credentials: Dict[str, APICredentials] = {}
        self.api_templates: Dict[str, Dict[str, Any]] = {}
        self.methodology_config: Optional[MethodologyConfig] = None
        self.system_config: Optional[SystemConfig] = None
        
        # Load existing configuration first
        self.load_configuration()
        
        # Then initialize API credential templates (which may use loaded config)
        self._init_api_templates()
    
    def _init_api_templates(self):
        """Initialize API credential templates from configuration file"""
        # Try to load API templates from configuration file
        try:
            if Path(self.config_path).exists():
                with open(self.config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                
                if config_data and 'api_templates' in config_data:
                    self.api_templates = config_data['api_templates']
                    logger.info(f"Loaded {len(self.api_templates)} API templates from configuration")
                    return
        except Exception as e:
            logger.warning(f"Failed to load API templates from config: {e}")
        
        # Fallback to hardcoded templates if not in config
        logger.warning("API templates not found in configuration, using fallback defaults")
        api_templates = {
            'yahoo_finance': {
                'description': 'Yahoo Finance API (yfinance library)',
                'required_fields': [],  # No credentials required for basic access
                'optional_fields': [],
                'test_endpoint': 'stock_info',
                'rate_limits': {'requests_per_hour': 2000}
            },
            'reddit': {
                'description': 'Reddit API for sentiment analysis',
                'required_fields': ['client_id', 'client_secret', 'user_agent'],
                'optional_fields': ['username', 'password'],
                'test_endpoint': 'subreddit_access',
                'rate_limits': {'requests_per_minute': 60}
            },
            'alpha_vantage': {
                'description': 'Alpha Vantage API for additional financial data',
                'required_fields': ['api_key'],
                'optional_fields': [],
                'test_endpoint': 'quote_data',
                'rate_limits': {'requests_per_minute': 5}
            },
            'news_api': {
                'description': 'News API for additional news sources',
                'required_fields': ['api_key'],
                'optional_fields': [],
                'test_endpoint': 'headlines',
                'rate_limits': {'requests_per_day': 1000}
            }
        }
        self.api_templates = api_templates
    
    def load_configuration(self) -> bool:
        """Load configuration from file"""
        try:
            if not Path(self.config_path).exists():
                logger.info(f"Configuration file not found: {self.config_path}. Creating default.")
                self._create_default_config()
                return True
            
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Load API credentials
            api_data = config_data.get('api_credentials', {})
            for api_name, cred_data in api_data.items():
                self.api_credentials[api_name] = APICredentials(
                    api_name=api_name,
                    credentials=cred_data.get('credentials', {}),
                    status=APIStatus(cred_data.get('status', 'untested')),
                    last_tested=datetime.fromisoformat(cred_data['last_tested']) if cred_data.get('last_tested') else None,
                    test_result=cred_data.get('test_result'),
                    rate_limit_info=cred_data.get('rate_limit_info', {})
                )
            
            # Load methodology configuration
            method_data = config_data.get('methodology', {})
            if method_data:
                self.methodology_config = MethodologyConfig(
                    component_weights=method_data.get('weights', {}),
                    scoring_thresholds=method_data.get('scoring_thresholds', {}),
                    quality_thresholds=method_data.get('quality_thresholds', {}),
                    staleness_limits=method_data.get('staleness_limits', {}),
                    sector_adjustments=method_data.get('sector_adjustments', {})
                )
            
            # Load system configuration
            sys_data = config_data.get('system', {})
            if sys_data:
                self.system_config = SystemConfig(
                    database_path=sys_data.get('database_path', 'data/stock_data.db'),
                    logging_level=sys_data.get('logging_level', 'INFO'),
                    cache_settings=sys_data.get('cache_settings', {}),
                    performance_settings=sys_data.get('performance_settings', {}),
                    backup_settings=sys_data.get('backup_settings', {})
                )
            
            logger.info("Configuration loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self._create_default_config()
            return False
    
    def save_configuration(self) -> bool:
        """Save current configuration to file"""
        try:
            config_data = {
                'api_credentials': {},
                'methodology': {},
                'system': {},
                'last_updated': datetime.now().isoformat()
            }
            
            # Save API credentials
            for api_name, cred in self.api_credentials.items():
                config_data['api_credentials'][api_name] = {
                    'credentials': cred.credentials,
                    'status': cred.status.value,
                    'last_tested': cred.last_tested.isoformat() if cred.last_tested else None,
                    'test_result': cred.test_result,
                    'rate_limit_info': cred.rate_limit_info
                }
            
            # Save methodology configuration
            if self.methodology_config:
                config_data['methodology'] = asdict(self.methodology_config)
            
            # Save system configuration
            if self.system_config:
                config_data['system'] = asdict(self.system_config)
            
            # Write to file
            with open(self.config_path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            
            logger.info("Configuration saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
    
    def _create_default_config(self):
        """Create default configuration"""
        # Default methodology configuration
        self.methodology_config = MethodologyConfig(
            component_weights={
                'fundamental': 0.40,
                'quality': 0.25,
                'growth': 0.20,
                'sentiment': 0.15
            },
            scoring_thresholds={
                'pe_ratio': {'excellent': 15, 'good': 20, 'average': 25, 'poor': 35},
                'ev_ebitda': {'excellent': 10, 'good': 15, 'average': 20, 'poor': 30},
                'peg_ratio': {'excellent': 0.5, 'good': 1.0, 'average': 1.5, 'poor': 2.0}
            },
            quality_thresholds={
                'minimum_data_quality': 0.6,
                'high_quality_threshold': 0.8,
                'excellent_quality_threshold': 0.9
            },
            staleness_limits={
                'fundamentals_days': 90,
                'price_days': 7,
                'news_days': 30,
                'sentiment_days': 14
            },
            sector_adjustments={
                'technology': {'pe_multiplier': 1.2, 'growth_weight': 1.1},
                'utilities': {'dividend_weight': 1.3, 'stability_weight': 1.2},
                'healthcare': {'quality_weight': 1.1, 'defensive_weight': 1.1}
            }
        )
        
        # Default system configuration
        self.system_config = SystemConfig(
            database_path='data/stock_data.db',
            logging_level='INFO',
            cache_settings={
                'enable_cache': True,
                'cache_duration_hours': 24,
                'max_cache_size_mb': 100
            },
            performance_settings={
                'max_concurrent_requests': 5,
                'request_timeout_seconds': 30,
                'retry_attempts': 3
            },
            backup_settings={
                'auto_backup': True,
                'backup_interval_hours': 24,
                'max_backup_files': 7
            }
        )
        
        # Initialize empty API credentials
        for api_name in self.api_templates.keys():
            self.api_credentials[api_name] = APICredentials(
                api_name=api_name,
                credentials={},
                status=APIStatus.UNTESTED,
                last_tested=None,
                test_result=None,
                rate_limit_info={}
            )
        
        # Save default configuration
        self.save_configuration()
    
    def test_api_credentials(self, api_name: str) -> Tuple[APIStatus, str]:
        """Test API credentials for a specific service"""
        if api_name not in self.api_credentials:
            return APIStatus.FAILED, f"Unknown API: {api_name}"
        
        cred = self.api_credentials[api_name]
        
        try:
            if api_name == 'yahoo_finance':
                return self._test_yahoo_finance()
            elif api_name == 'reddit':
                return self._test_reddit_api(cred.credentials)
            elif api_name == 'alpha_vantage':
                return self._test_alpha_vantage(cred.credentials)
            elif api_name == 'news_api':
                return self._test_news_api(cred.credentials)
            else:
                return APIStatus.FAILED, f"No test implementation for {api_name}"
                
        except Exception as e:
            logger.error(f"Error testing {api_name} API: {e}")
            return APIStatus.FAILED, str(e)
    
    def _test_yahoo_finance(self) -> Tuple[APIStatus, str]:
        """Test Yahoo Finance API access"""
        try:
            # Test with a known stock
            ticker = yf.Ticker("AAPL")
            info = ticker.info
            
            if info and 'symbol' in info:
                return APIStatus.HEALTHY, "Successfully retrieved stock data"
            else:
                return APIStatus.LIMITED, "Limited data access - some features may be restricted"
                
        except Exception as e:
            if "rate limit" in str(e).lower():
                return APIStatus.RATE_LIMITED, f"Rate limited: {e}"
            else:
                return APIStatus.FAILED, f"Connection failed: {e}"
    
    def _test_reddit_api(self, credentials: Dict[str, str]) -> Tuple[APIStatus, str]:
        """Test Reddit API credentials"""
        required_fields = ['client_id', 'client_secret', 'user_agent']
        
        for field in required_fields:
            if field not in credentials or not credentials[field]:
                return APIStatus.INVALID_CREDENTIALS, f"Missing required field: {field}"
        
        try:
            reddit = praw.Reddit(
                client_id=credentials['client_id'],
                client_secret=credentials['client_secret'],
                user_agent=credentials['user_agent']
            )
            
            # Test access to a public subreddit
            subreddit = reddit.subreddit('stocks')
            
            # Try to get a few posts to test access
            posts = list(subreddit.hot(limit=1))
            
            if posts:
                return APIStatus.HEALTHY, "Successfully connected to Reddit API"
            else:
                return APIStatus.LIMITED, "Connected but limited access to content"
                
        except Exception as e:
            error_str = str(e).lower()
            if "invalid" in error_str or "unauthorized" in error_str:
                return APIStatus.INVALID_CREDENTIALS, f"Invalid credentials: {e}"
            elif "rate limit" in error_str:
                return APIStatus.RATE_LIMITED, f"Rate limited: {e}"
            else:
                return APIStatus.FAILED, f"Connection failed: {e}"
    
    def _test_alpha_vantage(self, credentials: Dict[str, str]) -> Tuple[APIStatus, str]:
        """Test Alpha Vantage API credentials"""
        if 'api_key' not in credentials or not credentials['api_key']:
            return APIStatus.INVALID_CREDENTIALS, "Missing API key"
        
        try:
            import requests
            
            url = f"https://www.alphavantage.co/query"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': 'AAPL',
                'apikey': credentials['api_key']
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if 'Error Message' in data:
                return APIStatus.INVALID_CREDENTIALS, f"API Error: {data['Error Message']}"
            elif 'Note' in data and 'call frequency' in data['Note']:
                return APIStatus.RATE_LIMITED, "Rate limit exceeded"
            elif 'Global Quote' in data:
                return APIStatus.HEALTHY, "Successfully retrieved quote data"
            else:
                return APIStatus.LIMITED, "Connected but unexpected response format"
                
        except Exception as e:
            return APIStatus.FAILED, f"Connection failed: {e}"
    
    def _test_news_api(self, credentials: Dict[str, str]) -> Tuple[APIStatus, str]:
        """Test News API credentials"""
        if 'api_key' not in credentials or not credentials['api_key']:
            return APIStatus.INVALID_CREDENTIALS, "Missing API key"
        
        try:
            import requests
            
            url = "https://newsapi.org/v2/top-headlines"
            headers = {'X-API-Key': credentials['api_key']}
            params = {
                'category': 'business',
                'country': 'us',
                'pageSize': 1
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            data = response.json()
            
            if response.status_code == 401:
                return APIStatus.INVALID_CREDENTIALS, "Invalid API key"
            elif response.status_code == 429:
                return APIStatus.RATE_LIMITED, "Rate limit exceeded"
            elif data.get('status') == 'ok':
                return APIStatus.HEALTHY, f"Successfully retrieved {data.get('totalResults', 0)} articles"
            else:
                return APIStatus.FAILED, f"API Error: {data.get('message', 'Unknown error')}"
                
        except Exception as e:
            return APIStatus.FAILED, f"Connection failed: {e}"
    
    def update_api_credentials(self, api_name: str, credentials: Dict[str, str]) -> bool:
        """Update API credentials and test them"""
        try:
            if api_name not in self.api_credentials:
                self.api_credentials[api_name] = APICredentials(
                    api_name=api_name,
                    credentials={},
                    status=APIStatus.UNTESTED,
                    last_tested=None,
                    test_result=None,
                    rate_limit_info={}
                )
            
            # Update credentials
            self.api_credentials[api_name].credentials.update(credentials)
            
            # Test the updated credentials
            status, result = self.test_api_credentials(api_name)
            
            # Update test results
            self.api_credentials[api_name].status = status
            self.api_credentials[api_name].last_tested = datetime.now()
            self.api_credentials[api_name].test_result = result
            
            # Save configuration
            self.save_configuration()
            
            logger.info(f"Updated and tested credentials for {api_name}: {status.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating credentials for {api_name}: {e}")
            return False
    
    def get_api_status_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get summary of all API statuses"""
        summary = {}
        
        for api_name, cred in self.api_credentials.items():
            template = self.api_templates.get(api_name, {})
            
            summary[api_name] = {
                'description': template.get('description', api_name),
                'status': cred.status.value,
                'last_tested': cred.last_tested.isoformat() if cred.last_tested else None,
                'test_result': cred.test_result,
                'has_credentials': bool(cred.credentials),
                'required_fields': template.get('required_fields', []),
                'configured_fields': list(cred.credentials.keys()),
                'rate_limits': template.get('rate_limits', {}),
                'rate_limit_info': cred.rate_limit_info
            }
        
        return summary
    
    def validate_methodology_config(self) -> Tuple[bool, List[str]]:
        """Validate methodology configuration"""
        errors = []
        
        if not self.methodology_config:
            errors.append("No methodology configuration found")
            return False, errors
        
        # Validate component weights
        weights = self.methodology_config.component_weights
        weight_sum = sum(weights.values())
        
        if abs(weight_sum - 1.0) > 0.001:
            errors.append(f"Component weights must sum to 1.0 (current: {weight_sum:.3f})")
        
        required_components = ['fundamental', 'quality', 'growth', 'sentiment']
        for component in required_components:
            if component not in weights:
                errors.append(f"Missing weight for component: {component}")
            elif weights[component] < 0 or weights[component] > 1:
                errors.append(f"Invalid weight for {component}: {weights[component]} (must be 0-1)")
        
        # Validate quality thresholds
        quality_thresholds = self.methodology_config.quality_thresholds
        for threshold_name, value in quality_thresholds.items():
            if not 0 <= value <= 1:
                errors.append(f"Quality threshold {threshold_name} must be 0-1 (current: {value})")
        
        # Validate staleness limits
        staleness_limits = self.methodology_config.staleness_limits
        for limit_name, days in staleness_limits.items():
            if days < 1 or days > 365:
                errors.append(f"Staleness limit {limit_name} must be 1-365 days (current: {days})")
        
        return len(errors) == 0, errors
    
    def update_methodology_config(self, updates: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Update methodology configuration"""
        try:
            if not self.methodology_config:
                self._create_default_config()
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(self.methodology_config, key):
                    setattr(self.methodology_config, key, value)
            
            # Validate updated configuration
            is_valid, errors = self.validate_methodology_config()
            
            if is_valid:
                self.save_configuration()
                logger.info("Methodology configuration updated successfully")
                return True, []
            else:
                logger.error(f"Invalid methodology configuration: {errors}")
                return False, errors
                
        except Exception as e:
            error_msg = f"Error updating methodology configuration: {e}"
            logger.error(error_msg)
            return False, [error_msg]
    
    def export_configuration(self, export_path: str) -> bool:
        """Export configuration to file"""
        try:
            export_data = {
                'api_credentials': {},
                'methodology': asdict(self.methodology_config) if self.methodology_config else {},
                'system': asdict(self.system_config) if self.system_config else {},
                'export_timestamp': datetime.now().isoformat(),
                'export_version': '1.0'
            }
            
            # Export API credentials (without sensitive data)
            for api_name, cred in self.api_credentials.items():
                export_data['api_credentials'][api_name] = {
                    'status': cred.status.value,
                    'last_tested': cred.last_tested.isoformat() if cred.last_tested else None,
                    'test_result': cred.test_result,
                    'has_credentials': bool(cred.credentials),
                    'configured_fields': list(cred.credentials.keys())
                }
            
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Configuration exported to {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting configuration: {e}")
            return False
    
    def get_configuration_health(self) -> Dict[str, Any]:
        """Get overall configuration health status"""
        health = {
            'overall_status': 'healthy',
            'issues': [],
            'api_summary': {},
            'methodology_valid': False,
            'last_check': datetime.now().isoformat()
        }
        
        try:
            # Check API status
            api_summary = self.get_api_status_summary()
            health['api_summary'] = api_summary
            
            healthy_apis = 0
            total_apis = len(api_summary)
            
            for api_name, info in api_summary.items():
                if info['status'] == 'healthy':
                    healthy_apis += 1
                elif info['status'] in ['failed', 'invalid_credentials']:
                    health['issues'].append(f"{api_name} API: {info['test_result']}")
            
            # Check methodology configuration
            is_valid, errors = self.validate_methodology_config()
            health['methodology_valid'] = is_valid
            
            if not is_valid:
                health['issues'].extend(errors)
            
            # Determine overall status
            if health['issues']:
                if len(health['issues']) > 3:
                    health['overall_status'] = 'critical'
                else:
                    health['overall_status'] = 'warning'
            
            health['api_health_percentage'] = (healthy_apis / total_apis * 100) if total_apis > 0 else 0
            
        except Exception as e:
            health['overall_status'] = 'error'
            health['issues'].append(f"Health check failed: {e}")
        
        return health


# Convenience functions
def get_configuration_manager(config_path: Optional[str] = None) -> ConfigurationManager:
    """Get a configuration manager instance"""
    return ConfigurationManager(config_path)


def test_all_apis(config_manager: ConfigurationManager) -> Dict[str, Tuple[APIStatus, str]]:
    """Test all configured APIs"""
    results = {}
    
    for api_name in config_manager.api_credentials.keys():
        status, message = config_manager.test_api_credentials(api_name)
        results[api_name] = (status, message)
        
        # Update the stored results
        config_manager.api_credentials[api_name].status = status
        config_manager.api_credentials[api_name].last_tested = datetime.now()
        config_manager.api_credentials[api_name].test_result = message
    
    # Save updated results
    config_manager.save_configuration()
    
    return results