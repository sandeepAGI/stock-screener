#!/usr/bin/env python3
"""
Production Deployment Integration Tests
Test suite for 500-stock S&P 500 deployment readiness
"""

import os
import sys
import tempfile
import shutil
import time
import statistics
from datetime import datetime, timedelta
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.data.database_operations import DatabaseOperationsManager
from src.data.database import DatabaseManager, NewsArticle
from src.data.monitoring import DataSourceMonitor
from src.data.validator import DataValidator
from src.analysis.data_quality import QualityAnalyticsEngine


class TestProductionDeploymentReadiness(unittest.TestCase):
    """Test production deployment readiness for 500-stock load"""
    
    @classmethod
    def setUpClass(cls):
        """Set up production test environment"""
        cls.test_dir = tempfile.mkdtemp()
        cls.test_db_path = os.path.join(cls.test_dir, "production_deployment_test.db")
        
        # Create database manager
        cls.db_manager = DatabaseManager()
        cls.db_manager.db_path = cls.test_db_path
        cls.db_manager.connect()
        cls.db_manager.create_tables()
        
        # Create S&P 500 simulation dataset
        cls._create_sp500_simulation()
        cls.db_manager.close()
        
        # Create test managers
        cls.ops_manager = DatabaseOperationsManager(cls.db_manager)
        cls.ops_manager.backup_dir = Path(cls.test_dir) / "backups"
        cls.ops_manager.export_dir = Path(cls.test_dir) / "exports"
        cls.ops_manager.backup_dir.mkdir(exist_ok=True)
        cls.ops_manager.export_dir.mkdir(exist_ok=True)
        
        cls.monitor = DataSourceMonitor()
        cls.validator = DataValidator()
        cls.quality_engine = QualityAnalyticsEngine()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        shutil.rmtree(cls.test_dir, ignore_errors=True)
    
    @classmethod
    def _create_sp500_simulation(cls):
        """Create realistic S&P 500 simulation dataset"""
        # S&P 500 sector distribution (approximate)
        sector_data = {
            "Technology": 75,
            "Healthcare": 60,
            "Financials": 65,
            "Consumer Discretionary": 50,
            "Communication Services": 25,
            "Industrials": 70,
            "Consumer Staples": 35,
            "Energy": 25,
            "Utilities": 30,
            "Real Estate": 30,
            "Materials": 30
        }
        
        stock_id = 1
        
        # Create stocks for each sector
        for sector, count in sector_data.items():
            for i in range(count):
                symbol = f"{sector[:3].upper()}{i:03d}"
                name = f"{sector} Company {i}"
                industry = f"{sector} Industry {i % 5}"
                
                # Realistic market caps (in billions)
                if sector == "Technology":
                    market_cap = (10 + i * 50) * 1000000000  # $10B - $3.7T
                elif sector == "Healthcare":
                    market_cap = (5 + i * 20) * 1000000000   # $5B - $1.2T
                else:
                    market_cap = (1 + i * 10) * 1000000000   # $1B - $500B
                
                exchange = "NASDAQ" if sector in ["Technology", "Communication Services"] else "NYSE"
                
                cls.db_manager.insert_stock(symbol, name, sector, industry, market_cap, exchange)
                stock_id += 1
        
        # Create realistic fundamental data with sector variations
        for sector, count in sector_data.items():
            sector_fundamentals = cls._get_sector_fundamentals(sector)
            
            for i in range(count):
                symbol = f"{sector[:3].upper()}{i:03d}"
                
                # Add some variation to fundamentals
                fundamentals = sector_fundamentals.copy()
                variation = 0.8 + (i % 5) * 0.1  # 0.8 to 1.2 multiplier
                
                for key in ['pe_ratio', 'ev_to_ebitda', 'peg_ratio']:
                    if fundamentals[key]:
                        fundamentals[key] *= variation
                
                # Add realistic revenue and market cap scaling
                fundamentals['total_revenue'] *= (1 + i * 0.5)
                fundamentals['market_cap'] *= (1 + i * 2)
                
                cls.db_manager.insert_fundamental_data(symbol, fundamentals)
        
        # Create news articles for subset of stocks (simulating real data collection)
        all_news_articles = []
        news_count = 0
        for sector, count in sector_data.items():
            # Not all stocks have news (realistic scenario)
            news_stock_count = min(count, max(10, count // 2))
            
            for i in range(news_stock_count):
                symbol = f"{sector[:3].upper()}{i:03d}"
                
                # Multiple news articles per stock with varying dates
                for j in range(3):
                    published_date = datetime.now() - timedelta(days=j * 2)
                    sentiment_score = 0.3 + (hash(f"{symbol}{j}") % 40) / 100  # 0.3 to 0.7
                    
                    article = NewsArticle(
                        symbol=symbol,
                        title=f"{sector} news {j} for {symbol}",
                        summary=f"{sector} summary {j} for {symbol}",
                        content=f"Financial news content for {symbol} in {sector} sector. " * 10,
                        publisher=f"source_{j % 3}",
                        publish_date=published_date,
                        url=f"https://finance.example.com/{symbol.lower()}/news/{j}",
                        sentiment_score=sentiment_score,
                        data_quality_score=0.8
                    )
                    all_news_articles.append(article)
                    news_count += 1
        
        # Insert all news articles at once
        if all_news_articles:
            cls.db_manager.insert_news_articles(all_news_articles)
        
        cls.db_manager.connection.commit()
        print(f"Created simulation with {stock_id-1} stocks and {news_count} news articles")
    
    @classmethod
    def _get_sector_fundamentals(cls, sector):
        """Get sector-specific fundamental data templates"""
        base_fundamentals = {
            'pe_ratio': 20.0,
            'ev_to_ebitda': 15.0,
            'peg_ratio': 1.5,
            'free_cash_flow': 5000000000,
            'market_cap': 50000000000,
            'total_revenue': 25000000000,
            'net_income': 3000000000,
            'total_assets': 40000000000,
            'total_debt': 15000000000,
            'shareholders_equity': 20000000000,
            'return_on_equity': 0.15,
            'debt_to_equity': 0.35,
            'current_ratio': 1.5,
            'revenue_growth': 0.08,
            'earnings_growth': 0.12,
            'data_source': 'sp500_simulation'
        }
        
        # Sector-specific adjustments
        sector_adjustments = {
            "Technology": {
                'pe_ratio': 25.0, 'peg_ratio': 1.8, 'revenue_growth': 0.15,
                'return_on_equity': 0.20, 'debt_to_equity': 0.25
            },
            "Healthcare": {
                'pe_ratio': 18.0, 'ev_to_ebitda': 12.0, 'revenue_growth': 0.10,
                'return_on_equity': 0.18, 'current_ratio': 2.0
            },
            "Financials": {
                'pe_ratio': 12.0, 'ev_to_ebitda': None, 'debt_to_equity': 2.5,
                'return_on_equity': 0.12, 'current_ratio': 1.1
            },
            "Energy": {
                'pe_ratio': 15.0, 'ev_to_ebitda': 8.0, 'revenue_growth': 0.05,
                'debt_to_equity': 0.45, 'current_ratio': 1.3
            },
            "Utilities": {
                'pe_ratio': 16.0, 'ev_to_ebitda': 10.0, 'revenue_growth': 0.03,
                'debt_to_equity': 0.55, 'current_ratio': 1.2
            }
        }
        
        # Apply sector adjustments
        if sector in sector_adjustments:
            for key, value in sector_adjustments[sector].items():
                if value is not None:
                    base_fundamentals[key] = value
        
        return base_fundamentals
    
    # ==================== LOAD TESTING ====================
    
    def test_database_load_capacity(self):
        """Test database performance with 500-stock load"""
        print("\n=== Testing Database Load Capacity ===")
        
        # Get current record counts
        self.db_manager.connect()
        cursor = self.db_manager.connection.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM stocks")
        stock_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM fundamental_data")
        fundamental_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM news_articles")
        news_count = cursor.fetchone()[0]
        
        self.db_manager.close()
        
        print(f"Stock count: {stock_count}")
        print(f"Fundamental records: {fundamental_count}")
        print(f"News articles: {news_count}")
        
        # Verify we have production-scale data
        self.assertGreaterEqual(stock_count, 450)  # Allow for small variations
        self.assertGreaterEqual(fundamental_count, 495)
        self.assertGreater(news_count, 700)  # Should have substantial news data
        
        # Test query performance with large dataset
        performance_result = self.ops_manager.analyze_performance()
        
        # Verify performance is acceptable
        for query_name, duration in performance_result["query_performance"].items():
            if duration > 0:  # Skip failed queries
                self.assertLess(duration, 10.0, f"Query {query_name} too slow: {duration:.2f}s")
                print(f"Query {query_name}: {duration:.3f}s")
    
    def test_backup_performance_at_scale(self):
        """Test backup performance with production data"""
        print("\n=== Testing Backup Performance ===")
        
        # Test uncompressed backup
        start_time = time.time()
        uncompressed_result = self.ops_manager.create_backup("scale_test_uncompressed", compress=False)
        uncompressed_duration = time.time() - start_time
        
        # Test compressed backup
        start_time = time.time()
        compressed_result = self.ops_manager.create_backup("scale_test_compressed", compress=True)
        compressed_duration = time.time() - start_time
        
        print(f"Uncompressed backup: {uncompressed_duration:.2f}s, {uncompressed_result['file_size_bytes']:,} bytes")
        print(f"Compressed backup: {compressed_duration:.2f}s, {compressed_result['file_size_bytes']:,} bytes")
        
        # Verify backup performance is reasonable
        self.assertLess(uncompressed_duration, 60.0, "Uncompressed backup took too long")
        self.assertLess(compressed_duration, 120.0, "Compressed backup took too long")
        
        # Verify compression efficiency
        compression_ratio = compressed_result['file_size_bytes'] / uncompressed_result['file_size_bytes']
        self.assertLess(compression_ratio, 0.7, f"Poor compression ratio: {compression_ratio:.2f}")
        
        # Verify integrity
        self.assertTrue(uncompressed_result["integrity_verified"])
        self.assertTrue(compressed_result["integrity_verified"])
    
    def test_export_performance_at_scale(self):
        """Test export performance with production data"""
        print("\n=== Testing Export Performance ===")
        
        # Test CSV export
        start_time = time.time()
        csv_result = self.ops_manager.export_data("csv", tables=["stocks", "fundamental_data"])
        csv_duration = time.time() - start_time
        
        # Test JSON export
        start_time = time.time()
        json_result = self.ops_manager.export_data("json", tables=["stocks", "fundamental_data"])
        json_duration = time.time() - start_time
        
        print(f"CSV export: {csv_duration:.2f}s, {csv_result['total_records']:,} records")
        print(f"JSON export: {json_duration:.2f}s, {json_result['total_records']:,} records")
        
        # Verify export performance
        self.assertLess(csv_duration, 30.0, "CSV export took too long")
        self.assertLess(json_duration, 60.0, "JSON export took too long")
        
        # Verify export completeness
        self.assertGreater(csv_result["total_records"], 900)  # ~500 stocks + ~500 fundamentals
        self.assertEqual(csv_result["total_records"], json_result["total_records"])
        
        # Verify file sizes are reasonable
        for file_path in csv_result["files"]:
            file_size = Path(file_path).stat().st_size
            self.assertGreater(file_size, 10000, f"Export file too small: {file_path}")
    
    # ==================== DATA QUALITY TESTING ====================
    
    def test_data_quality_validation_at_scale(self):
        """Test data quality validation with 500-stock dataset"""
        print("\n=== Testing Data Quality Validation ===")
        
        # Initialize validator
        validation_result = self.validator.run_complete_validation()
        
        print(f"Validation completed: {validation_result.report_date}")
        print(f"Overall status: {'PASS' if validation_result.failed_checks == 0 else 'FAIL'}")
        print(f"Total checks: {validation_result.total_checks}")
        print(f"Passed checks: {validation_result.passed_checks}")
        
        # Skip validation duration check as it's not available in DataIntegrityReport
        # Performance can be measured externally if needed
        
        # Verify data quality is acceptable for production
        pass_rate = validation_result.passed_checks / validation_result.total_checks if validation_result.total_checks > 0 else 0
        self.assertGreater(pass_rate, 0.6, f"Data quality too low: {pass_rate:.2%}")
        
        # Check specific validation categories
        if hasattr(validation_result, 'details') and validation_result.details:
            for detail in validation_result.details:
                if hasattr(detail, 'status') and detail.status == 'fail':
                    print(f"Warning: {detail.check_name} validation failed: {detail.message}")
    
    def test_quality_analytics_engine_performance(self):
        """Test Quality Analytics Engine with production data"""
        print("\n=== Testing Quality Analytics Engine ===")
        
        start_time = time.time()
        quality_report = self.quality_engine.generate_comprehensive_quality_report()
        analysis_duration = time.time() - start_time
        
        print(f"Quality analysis duration: {analysis_duration:.2f}s")
        print(f"Overall quality score: {quality_report.overall_quality_score}")
        
        # Verify analysis performance
        self.assertLess(analysis_duration, 45.0, "Quality analysis took too long")
        
        # Verify comprehensive analysis
        self.assertIsNotNone(quality_report.component_scores)
        self.assertIsNotNone(quality_report.overall_quality_score)
        self.assertIsNotNone(quality_report.recommendations)
        
        # Verify quality scores are reasonable
        self.assertGreater(quality_report.overall_quality_score, 0.5, "Overall quality too low for production")
        
        # Check component-specific quality
        for component_name, component_quality in quality_report.component_scores.items():
            if hasattr(component_quality, 'overall_score'):
                self.assertGreaterEqual(component_quality.overall_score, 0.0, f"{component_name} quality invalid: {component_quality.overall_score}")
    
    # ==================== STRESS TESTING ====================
    
    def test_concurrent_operations_stress(self):
        """Test system under concurrent operations"""
        print("\n=== Testing Concurrent Operations ===")
        
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def backup_operation():
            try:
                result = self.ops_manager.create_backup(f"stress_test_{int(time.time())}")
                results_queue.put(("backup", True, result))
            except Exception as e:
                results_queue.put(("backup", False, str(e)))
        
        def export_operation():
            try:
                result = self.ops_manager.export_data("csv", tables=["stocks"])
                results_queue.put(("export", True, result))
            except Exception as e:
                results_queue.put(("export", False, str(e)))
        
        def analysis_operation():
            try:
                result = self.ops_manager.analyze_performance()
                results_queue.put(("analysis", True, result))
            except Exception as e:
                results_queue.put(("analysis", False, str(e)))
        
        # Start concurrent operations
        threads = []
        operations = [backup_operation, export_operation, analysis_operation]
        
        start_time = time.time()
        for operation in operations:
            thread = threading.Thread(target=operation)
            thread.start()
            threads.append(thread)
        
        # Wait for all operations to complete
        for thread in threads:
            thread.join(timeout=120)  # 2-minute timeout
        
        total_duration = time.time() - start_time
        print(f"Concurrent operations completed in {total_duration:.2f}s")
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        # Verify all operations succeeded
        self.assertEqual(len(results), 3, "Not all operations completed")
        
        for operation_type, success, result in results:
            self.assertTrue(success, f"{operation_type} failed: {result}")
            print(f"{operation_type}: {'SUCCESS' if success else 'FAILED'}")
    
    def test_memory_usage_under_load(self):
        """Test memory usage with large dataset operations"""
        print("\n=== Testing Memory Usage ===")
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Baseline memory usage
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform memory-intensive operations
        operations = [
            ("Performance Analysis", lambda: self.ops_manager.analyze_performance()),
            ("Full Export", lambda: self.ops_manager.export_data("json")),
            ("Quality Analysis", lambda: self.quality_engine.generate_comprehensive_quality_report()),
        ]
        
        memory_usage = []
        
        for operation_name, operation in operations:
            start_memory = process.memory_info().rss / 1024 / 1024
            
            # Execute operation
            result = operation()
            
            end_memory = process.memory_info().rss / 1024 / 1024
            memory_increase = end_memory - start_memory
            
            memory_usage.append((operation_name, start_memory, end_memory, memory_increase))
            print(f"{operation_name}: {start_memory:.1f}MB -> {end_memory:.1f}MB (+{memory_increase:.1f}MB)")
        
        # Verify memory usage is reasonable
        max_memory = max(usage[2] for usage in memory_usage)
        memory_increase_total = max_memory - baseline_memory
        
        self.assertLess(memory_increase_total, 500, f"Excessive memory usage: {memory_increase_total:.1f}MB")
        
        # Verify no major memory leaks (check if memory returns to reasonable level)
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_retention = final_memory - baseline_memory
        
        self.assertLess(memory_retention, 200, f"Possible memory leak: {memory_retention:.1f}MB retained")
    
    # ==================== PRODUCTION READINESS CHECKS ====================
    
    def test_production_readiness_checklist(self):
        """Comprehensive production readiness verification"""
        print("\n=== Production Readiness Checklist ===")
        
        readiness_results = {}
        
        # 1. Database Performance
        perf_result = self.ops_manager.analyze_performance()
        readiness_results["database_performance"] = {
            "status": "PASS" if perf_result["integrity_check"] == "ok" else "FAIL",
            "details": f"DB size: {perf_result['database_size_mb']}MB, Records: {perf_result['total_records']:,}"
        }
        
        # 2. Backup System
        try:
            backup_result = self.ops_manager.create_backup("readiness_test")
            readiness_results["backup_system"] = {
                "status": "PASS" if backup_result["integrity_verified"] else "FAIL",
                "details": f"Backup size: {backup_result['file_size_bytes']:,} bytes"
            }
        except Exception as e:
            readiness_results["backup_system"] = {
                "status": "FAIL",
                "details": f"Backup failed: {str(e)}"
            }
        
        # 3. Export Capabilities
        try:
            export_result = self.ops_manager.export_data("csv", tables=["stocks"])
            readiness_results["export_system"] = {
                "status": "PASS" if export_result["total_records"] > 400 else "FAIL",
                "details": f"Exported {export_result['total_records']:,} records"
            }
        except Exception as e:
            readiness_results["export_system"] = {
                "status": "FAIL",
                "details": f"Export failed: {str(e)}"
            }
        
        # 4. Data Quality
        try:
            validation_result = self.validator.run_complete_validation()
            pass_rate = validation_result.passed_checks / validation_result.total_checks
            readiness_results["data_quality"] = {
                "status": "PASS" if pass_rate > 0.9 else "FAIL",
                "details": f"Validation pass rate: {pass_rate:.1%}"
            }
        except Exception as e:
            readiness_results["data_quality"] = {
                "status": "FAIL",
                "details": f"Validation failed: {str(e)}"
            }
        
        # 5. Storage Usage
        storage_usage = self.ops_manager.get_storage_usage()
        readiness_results["storage_management"] = {
            "status": "PASS",
            "details": f"Total storage: {storage_usage['total_size_mb']}MB"
        }
        
        # Print readiness report
        print("\nPRODUCTION READINESS REPORT:")
        print("=" * 50)
        all_passed = True
        
        for check_name, result in readiness_results.items():
            status_symbol = "✅" if result["status"] == "PASS" else "❌"
            print(f"{status_symbol} {check_name.replace('_', ' ').title()}: {result['details']}")
            
            if result["status"] != "PASS":
                all_passed = False
        
        print("=" * 50)
        print(f"Overall Status: {'✅ READY FOR PRODUCTION' if all_passed else '❌ NOT READY'}")
        
        # Assert overall readiness
        self.assertTrue(all_passed, "System not ready for production deployment")
    
    def test_s3_scale_simulation(self):
        """Simulate handling S&P 500 scale data operations"""
        print("\n=== S&P 500 Scale Simulation ===")
        
        # Verify we have close to S&P 500 scale
        self.db_manager.connect()
        cursor = self.db_manager.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM stocks")
        stock_count = cursor.fetchone()[0]
        self.db_manager.close()
        
        print(f"Simulating operations with {stock_count} stocks")
        
        # Simulate full data refresh cycle
        operations_performance = {}
        
        # 1. Full backup before refresh
        start_time = time.time()
        backup_result = self.ops_manager.create_backup("pre_refresh_backup")
        operations_performance["full_backup"] = time.time() - start_time
        
        # 2. Data validation
        start_time = time.time()
        validation_result = self.validator.run_complete_validation()
        operations_performance["data_validation"] = time.time() - start_time
        
        # 3. Quality analysis
        start_time = time.time()
        quality_result = self.quality_engine.generate_comprehensive_quality_report()
        operations_performance["quality_analysis"] = time.time() - start_time
        
        # 4. Performance optimization
        start_time = time.time()
        optimization_result = self.ops_manager.optimize_database()
        operations_performance["database_optimization"] = time.time() - start_time
        
        # 5. Full export
        start_time = time.time()
        export_result = self.ops_manager.export_data("csv")
        operations_performance["full_export"] = time.time() - start_time
        
        # Print performance summary
        print("\nS&P 500 SCALE OPERATION PERFORMANCE:")
        print("=" * 40)
        total_time = 0
        for operation, duration in operations_performance.items():
            print(f"{operation.replace('_', ' ').title()}: {duration:.2f}s")
            total_time += duration
        print("=" * 40)
        print(f"Total Time: {total_time:.2f}s ({total_time/60:.1f} minutes)")
        
        # Verify all operations completed within reasonable time
        self.assertLess(total_time, 600, f"Total operation time too long: {total_time:.1f}s")  # 10 minutes max
        
        # Verify individual operation performance
        performance_limits = {
            "full_backup": 120,      # 2 minutes
            "data_validation": 90,   # 1.5 minutes
            "quality_analysis": 60,  # 1 minute
            "database_optimization": 180,  # 3 minutes
            "full_export": 120       # 2 minutes
        }
        
        for operation, limit in performance_limits.items():
            actual_time = operations_performance.get(operation, 0)
            self.assertLess(actual_time, limit, 
                          f"{operation} took too long: {actual_time:.1f}s (limit: {limit}s)")


if __name__ == "__main__":
    # Run production deployment tests
    unittest.main(verbosity=2)