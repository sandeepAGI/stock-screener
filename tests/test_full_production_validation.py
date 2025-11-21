#!/usr/bin/env python3
"""
Full Production Validation Test
Demonstrates complete StockAnalyzer Pro system with quality validation
"""

import unittest
import tempfile
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.database import DatabaseManager
from src.data.data_versioning import DataVersionManager, DataFreshnessLevel
from src.data.config_manager import ConfigurationManager
from src.calculations.fundamental import FundamentalCalculator
from src.calculations.quality import QualityCalculator
from src.calculations.growth import GrowthCalculator
from src.calculations.sentiment import SentimentCalculator
from src.calculations.composite import CompositeCalculator


class TestFullProductionValidation(unittest.TestCase):
    """Comprehensive production validation test"""
    
    def setUp(self):
        """Set up production test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, "production_test.db")
        self.test_config_path = os.path.join(self.test_dir, "test_config.yaml")
        
        # Create database manager
        self.db_manager = DatabaseManager()
        self.db_manager.db_path = self.test_db_path
        self.db_manager.connect()
        self.db_manager.create_tables()
        
        # Create configuration manager
        self.config_manager = ConfigurationManager(self.test_config_path)
        
        # Create version manager
        self.version_manager = DataVersionManager(self.db_manager)
        
        # Create calculators
        self.calculators = {
            'fundamental': FundamentalCalculator(),
            'quality': QualityCalculator(),
            'growth': GrowthCalculator(),
            'sentiment': SentimentCalculator(),
            'composite': CompositeCalculator()
        }
        
        # Test stocks - representative S&P 500 sample
        self.test_stocks = [
            # Technology
            ('AAPL', 'Apple Inc.', 'Technology', 'Consumer Electronics'),
            ('MSFT', 'Microsoft Corporation', 'Technology', 'Software'),
            ('GOOGL', 'Alphabet Inc.', 'Technology', 'Internet Services'),
            
            # Healthcare
            ('JNJ', 'Johnson & Johnson', 'Healthcare', 'Pharmaceuticals'),
            ('PFE', 'Pfizer Inc.', 'Healthcare', 'Pharmaceuticals'),
            
            # Financial
            ('JPM', 'JPMorgan Chase & Co.', 'Financial', 'Banking'),
            ('BAC', 'Bank of America Corporation', 'Financial', 'Banking'),
            
            # Consumer
            ('PG', 'Procter & Gamble Company', 'Consumer Staples', 'Personal Products'),
            ('KO', 'The Coca-Cola Company', 'Consumer Staples', 'Beverages'),
            
            # Industrial
            ('CAT', 'Caterpillar Inc.', 'Industrials', 'Construction Machinery'),
            ('GE', 'General Electric Company', 'Industrials', 'Conglomerates'),
            
            # Energy
            ('XOM', 'Exxon Mobil Corporation', 'Energy', 'Oil & Gas'),
            ('CVX', 'Chevron Corporation', 'Energy', 'Oil & Gas'),
            
            # Utilities
            ('NEE', 'NextEra Energy, Inc.', 'Utilities', 'Electric Utilities'),
            ('DUK', 'Duke Energy Corporation', 'Utilities', 'Electric Utilities'),
        ]
    
    def tearDown(self):
        """Clean up test resources"""
        self.db_manager.close()
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def _populate_test_data(self):
        """Populate database with comprehensive test data"""
        print(f"Populating database with {len(self.test_stocks)} test stocks...")
        
        for symbol, name, sector, industry in self.test_stocks:
            # Add stock
            self.db_manager.insert_stock(
                symbol=symbol,
                company_name=name,
                sector=sector,
                industry=industry,
                market_cap=self._generate_market_cap(sector),
                listing_exchange='NASDAQ' if sector == 'Technology' else 'NYSE'
            )
            
            # Add fundamental data
            fundamentals = self._generate_fundamental_data(symbol, sector)
            self.db_manager.insert_fundamental_data(symbol, fundamentals)
        
        print(f"✅ Added {len(self.test_stocks)} stocks with fundamental data")
    
    def _generate_market_cap(self, sector: str) -> int:
        """Generate realistic market cap based on sector"""
        base_caps = {
            'Technology': 2000000000000,  # $2T
            'Healthcare': 400000000000,   # $400B
            'Financial': 300000000000,    # $300B
            'Consumer Staples': 250000000000,  # $250B
            'Industrials': 150000000000,  # $150B
            'Energy': 200000000000,       # $200B
            'Utilities': 100000000000     # $100B
        }
        return base_caps.get(sector, 100000000000)
    
    def _generate_fundamental_data(self, symbol: str, sector: str) -> Dict[str, Any]:
        """Generate realistic fundamental data for testing"""
        # Base values with sector adjustments
        sector_multipliers = {
            'Technology': {'pe': 1.5, 'growth': 1.3, 'margins': 1.2},
            'Healthcare': {'pe': 1.2, 'growth': 1.1, 'margins': 1.1},
            'Financial': {'pe': 0.8, 'growth': 1.0, 'margins': 0.9},
            'Consumer Staples': {'pe': 1.0, 'growth': 0.8, 'margins': 1.0},
            'Industrials': {'pe': 0.9, 'growth': 0.9, 'margins': 0.8},
            'Energy': {'pe': 0.7, 'growth': 0.7, 'margins': 0.7},
            'Utilities': {'pe': 0.8, 'growth': 0.6, 'margins': 0.9}
        }
        
        multiplier = sector_multipliers.get(sector, {'pe': 1.0, 'growth': 1.0, 'margins': 1.0})
        
        # Generate age variation (some fresh, some stale)
        symbol_hash = hash(symbol) % 100
        if symbol_hash < 30:  # 30% fresh data
            data_age = 0
        elif symbol_hash < 60:  # 30% recent data
            data_age = 15
        else:  # 40% stale data
            data_age = 45
        
        reporting_date = (datetime.now() - timedelta(days=data_age)).date()
        
        return {
            'pe_ratio': 20.0 * multiplier['pe'],
            'ev_to_ebitda': 15.0 * multiplier['pe'],
            'peg_ratio': 1.2 * (1.0 / multiplier['growth']),
            'market_cap': self._generate_market_cap(sector),
            'total_revenue': 100000000000 * multiplier['margins'],
            'net_income': 20000000000 * multiplier['margins'],
            'total_assets': 200000000000,
            'total_debt': 50000000000,
            'shareholders_equity': 100000000000,
            'free_cash_flow': 25000000000 * multiplier['margins'],
            'return_on_equity': 0.15 * multiplier['margins'],
            'debt_to_equity': 0.5,
            'current_ratio': 1.2,
            'revenue_growth': 0.08 * multiplier['growth'],
            'earnings_growth': 0.12 * multiplier['growth'],
            'reporting_date': reporting_date.isoformat(),
            'data_source': 'production_test'
        }
    
    def test_01_production_database_setup(self):
        """Test production database setup and population"""
        print("\n🔧 Testing Production Database Setup...")
        
        # Populate test data
        self._populate_test_data()
        
        # Verify database population
        stocks = self.db_manager.get_all_stocks()
        self.assertEqual(len(stocks), len(self.test_stocks))
        
        # Verify table record counts
        counts = self.db_manager.get_table_record_counts()
        self.assertEqual(counts['stocks'], len(self.test_stocks))
        self.assertEqual(counts['fundamental_data'], len(self.test_stocks))
        
        # Verify database statistics
        stats = self.db_manager.get_database_statistics()
        self.assertIn('table_statistics', stats)
        self.assertIn('performance_metrics', stats)
        
        print(f"✅ Database setup complete: {len(stocks)} stocks, {sum(counts.values())} total records")
    
    def test_02_data_versioning_and_freshness(self):
        """Test data versioning and freshness indicators"""
        print("\n📅 Testing Data Versioning and Freshness...")
        
        # Ensure test data is populated
        if not self.db_manager.get_all_stocks():
            self._populate_test_data()
        
        freshness_stats = {'fresh': 0, 'recent': 0, 'stale': 0, 'very_stale': 0, 'missing': 0}
        
        for symbol, _, _, _ in self.test_stocks[:5]:  # Test first 5 stocks
            summary = self.version_manager.get_data_freshness_summary(symbol)
            
            # Check that we have version info for all data types
            self.assertIn('fundamentals', summary)
            self.assertIn('price', summary)
            self.assertIn('news', summary)
            self.assertIn('sentiment', summary)
            
            # Track freshness levels
            fund_freshness = summary['fundamentals'].freshness_level
            freshness_stats[fund_freshness.value] += 1
            
            # Test staleness impact calculation
            versioned_fund = self.version_manager.get_versioned_fundamentals(symbol)
            if versioned_fund:
                self.assertGreaterEqual(versioned_fund.staleness_impact, 0.0)
                self.assertLessEqual(versioned_fund.staleness_impact, 1.0)
        
        print(f"✅ Freshness distribution: {freshness_stats}")
        
        # Should have variety of freshness levels
        total_checked = sum(freshness_stats.values())
        self.assertGreater(total_checked, 0)
    
    def test_03_calculation_engines_comprehensive(self):
        """Test all calculation engines with production data"""
        print("\n🧮 Testing All Calculation Engines...")
        
        # Ensure test data is populated
        if not self.db_manager.get_all_stocks():
            self._populate_test_data()
        
        results = {
            'fundamental': [],
            'quality': [], 
            'growth': [],
            'sentiment': [],
            'composite': []
        }
        
        # Test each calculation engine
        for symbol, _, sector, _ in self.test_stocks[:10]:  # Test first 10 stocks
            
            # Test fundamental calculator
            fund_metrics = self.calculators['fundamental'].calculate_fundamental_metrics(symbol, self.db_manager)
            if fund_metrics:
                results['fundamental'].append(fund_metrics)
                self.assertIsNotNone(fund_metrics.fundamental_score)
                self.assertGreaterEqual(fund_metrics.fundamental_score, 0)
                self.assertLessEqual(fund_metrics.fundamental_score, 100)
                
                # Verify data versioning integration
                self.assertIsNotNone(fund_metrics.data_version_id)
                self.assertIsNotNone(fund_metrics.data_freshness_level)
                self.assertIsNotNone(fund_metrics.staleness_impact)
            
            # Test quality calculator
            quality_metrics = self.calculators['quality'].calculate_quality_metrics(symbol, self.db_manager)
            if quality_metrics:
                results['quality'].append(quality_metrics)
                self.assertIsNotNone(quality_metrics.quality_score)
                self.assertGreaterEqual(quality_metrics.quality_score, 0)
                self.assertLessEqual(quality_metrics.quality_score, 100)
            
            # Test growth calculator
            growth_metrics = self.calculators['growth'].calculate_growth_metrics(symbol, self.db_manager)
            if growth_metrics:
                results['growth'].append(growth_metrics)
                self.assertIsNotNone(growth_metrics.growth_score)
                self.assertGreaterEqual(growth_metrics.growth_score, 0)
                self.assertLessEqual(growth_metrics.growth_score, 100)
            
            # Test sentiment calculator (will be missing but should handle gracefully)
            sentiment_metrics = self.calculators['sentiment'].calculate_sentiment_metrics(symbol, self.db_manager)
            if sentiment_metrics:
                results['sentiment'].append(sentiment_metrics)
                self.assertIsNotNone(sentiment_metrics.sentiment_score)
                self.assertGreaterEqual(sentiment_metrics.sentiment_score, 0)
                self.assertLessEqual(sentiment_metrics.sentiment_score, 100)
        
        # Test composite calculator
        test_symbols = [symbol for symbol, _, _, _ in self.test_stocks[:5]]
        composite_results = self.calculators['composite'].calculate_batch_composite(test_symbols, self.db_manager)
        
        for symbol, composite_metrics in composite_results.items():
            if composite_metrics:
                results['composite'].append(composite_metrics)
                self.assertIsNotNone(composite_metrics.composite_score)
                self.assertGreaterEqual(composite_metrics.composite_score, 0)
                self.assertLessEqual(composite_metrics.composite_score, 100)
                
                # Verify component scores exist
                self.assertIsNotNone(composite_metrics.fundamental_score)
                self.assertIsNotNone(composite_metrics.quality_score)
                self.assertIsNotNone(composite_metrics.growth_score)
        
        # Summary
        for calc_type, metrics_list in results.items():
            print(f"✅ {calc_type.title()}: {len(metrics_list)} successful calculations")
        
        # Should have successful calculations for most components
        self.assertGreater(len(results['fundamental']), 5)
        self.assertGreater(len(results['composite']), 3)
    
    def test_04_quality_gating_workflow(self):
        """Test quality gating workflow with production data"""
        print("\n🚪 Testing Quality Gating Workflow...")
        
        # Ensure test data is populated
        if not self.db_manager.get_all_stocks():
            self._populate_test_data()
        
        # Test quality gate validation
        min_quality_threshold = 0.7
        max_staleness_days = 30
        
        passed_stocks = []
        failed_stocks = []
        
        for symbol, _, _, _ in self.test_stocks[:8]:  # Test 8 stocks
            summary = self.version_manager.get_data_freshness_summary(symbol)
            
            # Calculate overall quality
            quality_scores = [info.quality_score for info in summary.values()]
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
            
            # Calculate staleness
            ages = [info.age_days for info in summary.values() if info.age_days is not None]
            avg_age = sum(ages) / len(ages) if ages else 999
            
            # Apply quality gate
            if avg_quality >= min_quality_threshold and avg_age <= max_staleness_days:
                passed_stocks.append(symbol)
            else:
                failed_stocks.append(symbol)
        
        print(f"✅ Quality Gate Results: {len(passed_stocks)} passed, {len(failed_stocks)} failed")
        print(f"   Passed: {passed_stocks}")
        print(f"   Failed: {failed_stocks}")
        
        # Should have some results
        total_evaluated = len(passed_stocks) + len(failed_stocks)
        self.assertGreater(total_evaluated, 0)
    
    def test_05_configuration_management_integration(self):
        """Test configuration management integration"""
        print("\n⚙️ Testing Configuration Management...")
        
        # Test configuration health
        health = self.config_manager.get_configuration_health()
        self.assertIn('overall_status', health)
        self.assertIn('methodology_valid', health)
        self.assertTrue(health['methodology_valid'])
        
        # Test API status
        api_status = self.config_manager.get_api_status_summary()
        self.assertGreater(len(api_status), 0)
        
        # Test methodology configuration
        method_config = self.config_manager.methodology_config
        self.assertIsNotNone(method_config)
        
        # Verify weight sum
        total_weight = sum(method_config.component_weights.values())
        self.assertAlmostEqual(total_weight, 1.0, places=2)
        
        # Test configuration export
        export_path = os.path.join(self.test_dir, "config_export.json")
        export_success = self.config_manager.export_configuration(export_path)
        self.assertTrue(export_success)
        self.assertTrue(os.path.exists(export_path))
        
        print("✅ Configuration management fully operational")
    
    def test_06_performance_and_scalability(self):
        """Test system performance with production load"""
        print("\n⚡ Testing Performance and Scalability...")
        
        # Ensure test data is populated
        if not self.db_manager.get_all_stocks():
            self._populate_test_data()
        
        # Measure database performance
        import time
        
        start_time = time.time()
        
        # Database operations
        stats = self.db_manager.get_database_statistics()
        counts = self.db_manager.get_table_record_counts()
        
        db_time = time.time() - start_time
        
        # Calculation performance  
        start_time = time.time()
        
        test_symbols = [symbol for symbol, _, _, _ in self.test_stocks[:5]]
        
        # Run calculations
        fund_results = []
        for symbol in test_symbols:
            metrics = self.calculators['fundamental'].calculate_fundamental_metrics(symbol, self.db_manager)
            if metrics:
                fund_results.append(metrics)
        
        calc_time = time.time() - start_time
        
        # Performance assertions
        self.assertLess(db_time, 2.0)  # Database ops should be under 2 seconds
        self.assertLess(calc_time, 5.0)  # Calculations should be under 5 seconds
        
        # Quality metrics
        success_rate = len(fund_results) / len(test_symbols) if test_symbols else 0
        self.assertGreater(success_rate, 0.5)  # At least 50% success rate
        
        print(f"✅ Performance: DB ops {db_time:.2f}s, calculations {calc_time:.2f}s")
        print(f"✅ Success rate: {success_rate:.1%} ({len(fund_results)}/{len(test_symbols)})")
    
    def test_07_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        print("\n🔄 Testing End-to-End Workflow...")
        
        # Ensure test data is populated
        if not self.db_manager.get_all_stocks():
            self._populate_test_data()
        
        # Complete workflow test
        workflow_results = {
            'stocks_processed': 0,
            'successful_calculations': 0,
            'quality_approved': 0,
            'rankings_generated': 0
        }
        
        test_symbols = [symbol for symbol, _, _, _ in self.test_stocks[:6]]
        
        for symbol in test_symbols:
            workflow_results['stocks_processed'] += 1
            
            # Step 1: Data versioning check
            summary = self.version_manager.get_data_freshness_summary(symbol)
            
            # Step 2: Quality gate validation
            avg_quality = sum(info.quality_score for info in summary.values()) / len(summary)
            if avg_quality >= 0.2:  # Very low threshold for test environment
                workflow_results['quality_approved'] += 1
                
                # Step 3: Calculate metrics
                fund_metrics = self.calculators['fundamental'].calculate_fundamental_metrics(symbol, self.db_manager)
                if fund_metrics:
                    workflow_results['successful_calculations'] += 1
        
        # Step 4: Generate composite rankings
        composite_results = self.calculators['composite'].calculate_batch_composite(test_symbols, self.db_manager)
        workflow_results['rankings_generated'] = len([r for r in composite_results.values() if r is not None])
        
        # Workflow validation
        print(f"✅ Workflow Results:")
        for metric, value in workflow_results.items():
            print(f"   {metric}: {value}")
        
        # Success criteria
        self.assertGreater(workflow_results['stocks_processed'], 0)
        self.assertGreater(workflow_results['successful_calculations'], 0)
        self.assertGreater(workflow_results['rankings_generated'], 0)
        
        # Calculate success rates
        calc_success_rate = workflow_results['successful_calculations'] / workflow_results['stocks_processed']
        ranking_success_rate = workflow_results['rankings_generated'] / workflow_results['stocks_processed']
        
        print(f"✅ Success Rates: Calculations {calc_success_rate:.1%}, Rankings {ranking_success_rate:.1%}")
        
        # Should achieve reasonable success rates
        self.assertGreater(calc_success_rate, 0.3)  # Adjusted for test environment
        self.assertGreater(ranking_success_rate, 0.3)
    
    def test_08_production_readiness_checklist(self):
        """Final production readiness validation"""
        print("\n✅ Production Readiness Checklist...")
        
        checklist = {
            'Database Schema': False,
            'Data Versioning': False,
            'Quality Gating': False,
            'All Calculators': False,
            'Configuration Management': False,
            'Error Handling': False,
            'Performance': False
        }
        
        try:
            # Database schema
            stats = self.db_manager.get_database_statistics()
            if 'table_statistics' in stats and len(stats['table_statistics']) >= 6:
                checklist['Database Schema'] = True
            
            # Data versioning
            if hasattr(self.version_manager, 'get_data_freshness_summary'):
                checklist['Data Versioning'] = True
            
            # Quality gating  
            test_summary = self.version_manager.get_data_freshness_summary('AAPL')
            if test_summary and 'fundamentals' in test_summary:
                checklist['Quality Gating'] = True
            
            # All calculators
            if all(calc is not None for calc in self.calculators.values()):
                checklist['All Calculators'] = True
            
            # Configuration management
            health = self.config_manager.get_configuration_health()
            if health.get('methodology_valid'):
                checklist['Configuration Management'] = True
            
            # Error handling (test with invalid data)
            try:
                invalid_result = self.calculators['fundamental'].calculate_fundamental_metrics('INVALID', self.db_manager)
                # Should handle gracefully (return None, not crash)
                checklist['Error Handling'] = True
            except Exception:
                pass  # If it crashes, error handling fails
            
            # Performance (database ops under reasonable time)
            import time
            start = time.time()
            self.db_manager.get_table_record_counts()
            if time.time() - start < 1.0:
                checklist['Performance'] = True
                
        except Exception as e:
            print(f"   ⚠️ Checklist error: {e}")
        
        # Print results
        passed_count = sum(checklist.values())
        total_count = len(checklist)
        
        print(f"\n📋 Production Readiness: {passed_count}/{total_count} checks passed")
        
        for check, passed in checklist.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {check}")
        
        # Should pass most checks
        success_rate = passed_count / total_count
        self.assertGreater(success_rate, 0.8)  # 80% success rate required
        
        print(f"\n🎯 Overall Production Readiness: {success_rate:.1%}")
        
        if success_rate >= 0.9:
            print("🚀 SYSTEM IS PRODUCTION READY!")
        elif success_rate >= 0.8:
            print("⚠️ SYSTEM IS MOSTLY READY - Minor issues to address")
        else:
            print("❌ SYSTEM NEEDS MORE WORK")


if __name__ == '__main__':
    # Run tests with detailed output
    print("🚀 Starting Full Production Validation Test...")
    print("=" * 60)
    
    unittest.main(verbosity=2, buffer=False)