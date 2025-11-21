#!/usr/bin/env python3
"""
Tests for Data Versioning and Staleness Management System
"""

import unittest
import tempfile
import os
from datetime import datetime, timedelta
from src.data.database import DatabaseManager
from src.data.data_versioning import DataVersionManager, DataFreshnessLevel
from src.calculations.fundamental import FundamentalCalculator


class TestDataVersioning(unittest.TestCase):
    """Test data versioning and staleness detection"""
    
    def setUp(self):
        """Set up test database with sample data"""
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, "test_versioning.db")
        
        # Create database manager
        self.db_manager = DatabaseManager()
        self.db_manager.db_path = self.test_db_path
        self.db_manager.connect()
        self.db_manager.create_tables()
        
        # Create version manager
        self.version_manager = DataVersionManager(self.db_manager)
        
        # Add test stock
        self.test_symbol = "AAPL"
        self.db_manager.insert_stock(
            symbol=self.test_symbol,
            company_name="Apple Inc.",
            sector="Technology",
            industry="Consumer Electronics",
            market_cap=3000000000000,
            listing_exchange="NASDAQ"
        )
        
    def tearDown(self):
        """Clean up test resources"""
        self.db_manager.close()
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_fresh_data_detection(self):
        """Test detection of fresh data"""
        # Insert recent fundamental data (today)
        recent_date = datetime.now()
        fundamentals = {
            'pe_ratio': 25.0,
            'market_cap': 3000000000000,
            'total_revenue': 394000000000,
            'net_income': 99000000000,
            'total_assets': 353000000000,
            'total_debt': 120000000000,
            'shareholders_equity': 63000000000,
            'free_cash_flow': 92000000000,
            'return_on_equity': 0.175,
            'debt_to_equity': 1.9,
            'current_ratio': 1.0,
            'revenue_growth': 0.02,
            'earnings_growth': 0.05,
            'data_source': 'test',
            'reporting_date': recent_date.date().isoformat()
        }
        
        self.db_manager.insert_fundamental_data(self.test_symbol, fundamentals)
        
        # Get versioned data
        versioned_data = self.version_manager.get_versioned_fundamentals(self.test_symbol)
        
        self.assertIsNotNone(versioned_data)
        self.assertEqual(versioned_data.version_info.freshness_level, DataFreshnessLevel.FRESH)
        self.assertEqual(versioned_data.staleness_impact, 1.0)
        self.assertEqual(len(versioned_data.version_info.staleness_warnings), 0)
    
    def test_stale_data_detection(self):
        """Test detection of stale data"""
        # Insert old fundamental data (35 days ago)
        old_date = datetime.now() - timedelta(days=35)
        fundamentals = {
            'pe_ratio': 25.0,
            'market_cap': 3000000000000,
            'total_revenue': 394000000000,
            'net_income': 99000000000,
            'total_assets': 353000000000,
            'total_debt': 120000000000,
            'shareholders_equity': 63000000000,
            'free_cash_flow': 92000000000,
            'return_on_equity': 0.175,
            'debt_to_equity': 1.9,
            'current_ratio': 1.0,
            'revenue_growth': 0.02,
            'earnings_growth': 0.05,
            'data_source': 'test',
            'reporting_date': old_date.date().isoformat(),
            'data_collected_at': old_date.isoformat()
        }
        
        self.db_manager.insert_fundamental_data(self.test_symbol, fundamentals)
        
        # Get versioned data
        versioned_data = self.version_manager.get_versioned_fundamentals(self.test_symbol)
        
        self.assertIsNotNone(versioned_data)
        self.assertEqual(versioned_data.version_info.freshness_level, DataFreshnessLevel.STALE)
        self.assertLess(versioned_data.staleness_impact, 1.0)
        self.assertGreater(len(versioned_data.version_info.staleness_warnings), 0)
    
    def test_age_limit_filtering(self):
        """Test that age limits filter out old data"""
        # Insert old fundamental data (40 days ago)
        old_date = datetime.now() - timedelta(days=40)
        fundamentals = {
            'pe_ratio': 25.0,
            'market_cap': 3000000000000,
            'reporting_date': old_date.date().isoformat(),
            'data_collected_at': old_date.isoformat(),
            'data_source': 'test'
        }
        
        self.db_manager.insert_fundamental_data(self.test_symbol, fundamentals)
        
        # Request data with age limit of 30 days
        versioned_data = self.version_manager.get_versioned_fundamentals(self.test_symbol, max_age_days=30)
        
        # Should return None due to age limit
        self.assertIsNone(versioned_data)
    
    def test_missing_data_handling(self):
        """Test handling of missing data"""
        # Don't insert any data
        versioned_data = self.version_manager.get_versioned_fundamentals("NONEXISTENT")
        
        self.assertIsNotNone(versioned_data)
        self.assertEqual(versioned_data.version_info.freshness_level, DataFreshnessLevel.MISSING)
        self.assertEqual(versioned_data.staleness_impact, 0.0)
        self.assertGreater(len(versioned_data.version_info.staleness_warnings), 0)
    
    def test_fundamental_calculator_with_versioning(self):
        """Test fundamental calculator with data versioning enabled"""
        # Insert recent fundamental data
        recent_date = datetime.now()
        fundamentals = {
            'pe_ratio': 25.0,
            'ev_to_ebitda': 18.0,
            'peg_ratio': 1.5,
            'market_cap': 3000000000000,
            'total_revenue': 394000000000,
            'net_income': 99000000000,
            'total_assets': 353000000000,
            'total_debt': 120000000000,
            'shareholders_equity': 63000000000,
            'free_cash_flow': 92000000000,
            'return_on_equity': 0.175,
            'debt_to_equity': 1.9,
            'current_ratio': 1.0,
            'revenue_growth': 0.02,
            'earnings_growth': 0.05,
            'data_source': 'test',
            'reporting_date': recent_date.date().isoformat()
        }
        
        self.db_manager.insert_fundamental_data(self.test_symbol, fundamentals)
        
        # Calculate metrics with versioning
        calculator = FundamentalCalculator()
        metrics = calculator.calculate_fundamental_metrics(self.test_symbol, self.db_manager)
        
        self.assertIsNotNone(metrics)
        self.assertIsNotNone(metrics.data_version_id)
        self.assertEqual(metrics.data_freshness_level, DataFreshnessLevel.FRESH.value)
        self.assertAlmostEqual(metrics.staleness_impact, 1.0, places=2)
        self.assertIsNotNone(metrics.data_age_days)
        self.assertLess(metrics.data_age_days, 1.0)  # Should be very recent
    
    def test_freshness_summary(self):
        """Test data freshness summary for all data types"""
        # Insert some test data for different types
        recent_date = datetime.now()
        
        # Fundamental data
        fundamentals = {
            'pe_ratio': 25.0,
            'market_cap': 3000000000000,
            'reporting_date': recent_date.date().isoformat(),
            'data_collected_at': recent_date.isoformat(),
            'data_source': 'test'
        }
        self.db_manager.insert_fundamental_data(self.test_symbol, fundamentals)
        
        # Price data - insert directly into database
        cursor = self.db_manager.connection.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO price_data 
            (symbol, date, open, high, low, close, volume, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (self.test_symbol, recent_date.date().isoformat(), 150.0, 155.0, 149.0, 152.0, 50000000, 'test'))
        self.db_manager.connection.commit()
        
        # Get freshness summary
        summary = self.version_manager.get_data_freshness_summary(self.test_symbol)
        
        self.assertIn('fundamentals', summary)
        self.assertIn('price', summary)
        self.assertIn('news', summary)
        self.assertIn('sentiment', summary)
        
        # Fundamental and price should be fresh, news and sentiment missing
        self.assertEqual(summary['fundamentals'].freshness_level, DataFreshnessLevel.FRESH)
        self.assertEqual(summary['price'].freshness_level, DataFreshnessLevel.FRESH)
        self.assertEqual(summary['news'].freshness_level, DataFreshnessLevel.MISSING)
        self.assertEqual(summary['sentiment'].freshness_level, DataFreshnessLevel.MISSING)
    
    def test_staleness_report_generation(self):
        """Test generation of staleness report for multiple symbols"""
        symbols = ["AAPL", "MSFT"]
        
        # Add second stock
        self.db_manager.insert_stock(
            symbol="MSFT",
            company_name="Microsoft Corporation",
            sector="Technology",
            industry="Software",
            market_cap=2500000000000,
            listing_exchange="NASDAQ"
        )
        
        # Insert recent data for AAPL, old data for MSFT
        recent_date = datetime.now()
        old_date = datetime.now() - timedelta(days=45)
        
        # AAPL - fresh data
        fundamentals_aapl = {
            'pe_ratio': 25.0,
            'market_cap': 3000000000000,
            'reporting_date': recent_date.date().isoformat(),
            'data_collected_at': recent_date.isoformat(),
            'data_source': 'test'
        }
        self.db_manager.insert_fundamental_data("AAPL", fundamentals_aapl)
        
        # MSFT - stale data
        fundamentals_msft = {
            'pe_ratio': 20.0,
            'market_cap': 2500000000000,
            'reporting_date': old_date.date().isoformat(),
            'data_collected_at': old_date.isoformat(),
            'data_source': 'test'
        }
        self.db_manager.insert_fundamental_data("MSFT", fundamentals_msft)
        
        # Generate staleness report
        report = self.version_manager.generate_staleness_report(symbols)
        
        self.assertIn('report_date', report)
        self.assertEqual(report['symbols_analyzed'], 2)
        self.assertIn('freshness_summary', report)
        self.assertIn('stale_data_warnings', report)
        self.assertIn('recommendations', report)
        
        # Should have warnings for stale MSFT data
        msft_warnings = [w for w in report['stale_data_warnings'] if 'MSFT' in w]
        self.assertGreater(len(msft_warnings), 0)


if __name__ == '__main__':
    unittest.main()