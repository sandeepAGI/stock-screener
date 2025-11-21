#!/usr/bin/env python3
"""
Comprehensive Unit Tests for Database Operations Manager
Production-critical testing with full coverage
"""

import os
import sys
import tempfile
import shutil
import sqlite3
import gzip
import json
from pathlib import Path
from datetime import datetime, timedelta
import unittest
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.data.database_operations import DatabaseOperationsManager
from src.data.database import DatabaseManager, NewsArticle


class TestDatabaseOperationsManager(unittest.TestCase):
    """Test suite for Database Operations Manager"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary directory for tests
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, "test_stock_data.db")
        
        # Create test database with sample data
        self.db_manager = DatabaseManager()
        self.db_manager.db_path = self.test_db_path
        self.db_manager.connect()
        self.db_manager.create_tables()
        
        # Insert sample data
        self._create_sample_data()
        self.db_manager.close()
        
        # Create Database Operations Manager
        self.ops_manager = DatabaseOperationsManager(self.db_manager)
        self.ops_manager.backup_dir = Path(self.test_dir) / "backups"
        self.ops_manager.export_dir = Path(self.test_dir) / "exports"
        self.ops_manager.backup_dir.mkdir(exist_ok=True)
        self.ops_manager.export_dir.mkdir(exist_ok=True)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def _create_sample_data(self):
        """Create sample data for testing"""
        # Insert sample stocks
        sample_stocks = [
            ("AAPL", "Apple Inc.", "Technology", "Technology Hardware", 3000000000000, "NASDAQ"),
            ("MSFT", "Microsoft Corporation", "Technology", "Software", 2800000000000, "NASDAQ"),
            ("GOOGL", "Alphabet Inc.", "Communication Services", "Internet Content", 1800000000000, "NASDAQ")
        ]
        
        for stock in sample_stocks:
            self.db_manager.insert_stock(*stock)
        
        # Insert sample fundamental data
        sample_fundamentals = {
            'pe_ratio': 25.0,
            'ev_to_ebitda': 18.0,
            'peg_ratio': 1.5,
            'free_cash_flow': 80000000000,
            'market_cap': 3000000000000,
            'total_revenue': 400000000000,
            'net_income': 100000000000,
            'total_assets': 350000000000,
            'total_debt': 120000000000,
            'shareholders_equity': 60000000000,
            'return_on_equity': 0.18,
            'debt_to_equity': 0.3,
            'current_ratio': 1.8,
            'revenue_growth': 0.08,
            'earnings_growth': 0.12,
            'data_source': 'test_data'
        }
        
        for symbol in ["AAPL", "MSFT", "GOOGL"]:
            self.db_manager.insert_fundamental_data(symbol, sample_fundamentals)
        
        # Insert sample news data
        news_articles = []
        for i, symbol in enumerate(["AAPL", "MSFT", "GOOGL"]):
            article = NewsArticle(
                symbol=symbol,
                title=f"Test news for {symbol}",
                summary=f"Test summary for {symbol}",
                content=f"Test content for {symbol}",
                publisher="test_source",
                publish_date=datetime.now() - timedelta(days=i),
                url=f"http://test.com/{symbol}/{i}",
                sentiment_score=0.5,
                data_quality_score=0.8
            )
            news_articles.append(article)
        
        if news_articles:
            self.db_manager.insert_news_articles(news_articles)
        
        self.db_manager.connection.commit()
    
    # ==================== BACKUP OPERATIONS TESTS ====================
    
    def test_create_backup_uncompressed(self):
        """Test creating uncompressed backup"""
        result = self.ops_manager.create_backup("test_backup_uncompressed", compress=False)
        
        # Verify backup metadata
        self.assertEqual(result["backup_name"], "test_backup_uncompressed")
        self.assertFalse(result["compressed"])
        self.assertTrue(result["integrity_verified"])
        self.assertGreater(result["file_size_bytes"], 0)
        self.assertIsNotNone(result["checksum"])
        
        # Verify backup file exists
        backup_file = self.ops_manager.backup_dir / "test_backup_uncompressed.db"
        self.assertTrue(backup_file.exists())
        
        # Verify metadata file exists
        metadata_file = self.ops_manager.backup_dir / "test_backup_uncompressed_metadata.json"
        self.assertTrue(metadata_file.exists())
        
        # Verify record counts
        self.assertEqual(result["record_counts"]["stocks"], 3)
        self.assertEqual(result["record_counts"]["news_articles"], 3)
    
    def test_create_backup_compressed(self):
        """Test creating compressed backup"""
        result = self.ops_manager.create_backup("test_backup_compressed", compress=True)
        
        # Verify backup metadata
        self.assertEqual(result["backup_name"], "test_backup_compressed")
        self.assertTrue(result["compressed"])
        self.assertTrue(result["integrity_verified"])
        self.assertGreater(result["file_size_bytes"], 0)
        
        # Verify compressed backup file exists
        backup_file = self.ops_manager.backup_dir / "test_backup_compressed.db.gz"
        self.assertTrue(backup_file.exists())
        
        # Verify it's actually compressed (should be smaller than original)
        original_size = Path(self.test_db_path).stat().st_size
        compressed_size = backup_file.stat().st_size
        self.assertLess(compressed_size, original_size)
    
    def test_create_backup_auto_naming(self):
        """Test backup with automatic naming"""
        result = self.ops_manager.create_backup()
        
        # Verify auto-generated name follows pattern
        self.assertTrue(result["backup_name"].startswith("backup_"))
        self.assertRegex(result["backup_name"], r"backup_\d{8}_\d{6}")
    
    def test_restore_backup_uncompressed(self):
        """Test restoring from uncompressed backup"""
        # Create backup
        backup_result = self.ops_manager.create_backup("test_restore", compress=False)
        
        # Modify original database
        self.db_manager.connect()
        cursor = self.db_manager.connection.cursor()
        cursor.execute("DELETE FROM stocks WHERE symbol = 'AAPL'")
        self.db_manager.connection.commit()
        self.db_manager.close()
        
        # Restore backup
        restore_result = self.ops_manager.restore_backup("test_restore")
        
        # Verify restoration
        self.assertEqual(restore_result["backup_name"], "test_restore")
        self.assertTrue(restore_result["count_verification"])
        self.assertEqual(restore_result["restored_counts"]["stocks"], 3)
        
        # Verify AAPL is back in database
        self.db_manager.connect()
        cursor = self.db_manager.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM stocks WHERE symbol = 'AAPL'")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 1)
        self.db_manager.close()
    
    def test_restore_backup_compressed(self):
        """Test restoring from compressed backup"""
        # Create compressed backup
        backup_result = self.ops_manager.create_backup("test_restore_compressed", compress=True)
        
        # Clear database
        self.db_manager.connect()
        cursor = self.db_manager.connection.cursor()
        cursor.execute("DELETE FROM stocks")
        self.db_manager.connection.commit()
        self.db_manager.close()
        
        # Restore backup
        restore_result = self.ops_manager.restore_backup("test_restore_compressed")
        
        # Verify restoration
        self.assertTrue(restore_result["count_verification"])
        self.assertEqual(restore_result["restored_counts"]["stocks"], 3)
    
    def test_restore_nonexistent_backup(self):
        """Test restoring from non-existent backup"""
        with self.assertRaises(FileNotFoundError):
            self.ops_manager.restore_backup("nonexistent_backup")
    
    # ==================== EXPORT OPERATIONS TESTS ====================
    
    def test_export_csv(self):
        """Test CSV export functionality"""
        result = self.ops_manager.export_data("csv")
        
        # Verify export metadata
        self.assertEqual(result["format"], "csv")
        self.assertGreater(result["total_records"], 0)
        self.assertGreater(len(result["files"]), 0)
        
        # Verify CSV files exist and have content
        for file_path in result["files"]:
            self.assertTrue(Path(file_path).exists())
            self.assertGreater(Path(file_path).stat().st_size, 0)
        
        # Verify specific table export
        stocks_csv = None
        for file_path in result["files"]:
            if "stocks" in file_path:
                stocks_csv = file_path
                break
        
        self.assertIsNotNone(stocks_csv)
        
        # Check CSV content
        with open(stocks_csv, 'r') as f:
            lines = f.readlines()
            self.assertGreater(len(lines), 1)  # Header + data
            self.assertIn("symbol", lines[0].lower())  # Verify header
    
    def test_export_json(self):
        """Test JSON export functionality"""
        result = self.ops_manager.export_data("json")
        
        # Verify export metadata
        self.assertEqual(result["format"], "json")
        self.assertGreater(result["total_records"], 0)
        self.assertEqual(len(result["files"]), 1)  # Single JSON file
        
        # Verify JSON file exists and has valid content
        json_file = Path(result["files"][0])
        self.assertTrue(json_file.exists())
        
        with open(json_file, 'r') as f:
            data = json.load(f)
            self.assertIn("stocks", data)
            self.assertGreater(len(data["stocks"]), 0)
            self.assertEqual(len(data["stocks"]), 3)
    
    def test_export_with_filters(self):
        """Test export with data filters"""
        filters = {
            "stocks": {"sector": "Technology"}
        }
        
        result = self.ops_manager.export_data("json", filters=filters)
        
        # Verify filtered export
        json_file = Path(result["files"][0])
        with open(json_file, 'r') as f:
            data = json.load(f)
            
            # All stocks should be Technology sector
            for stock in data["stocks"]:
                self.assertEqual(stock["sector"], "Technology")
    
    def test_export_specific_tables(self):
        """Test exporting specific tables only"""
        result = self.ops_manager.export_data("csv", tables=["stocks", "fundamental_data"])
        
        # Verify only specified tables exported
        table_names = set()
        for file_path in result["files"]:
            filename = Path(file_path).stem
            for table in ["stocks", "fundamental_data", "news_articles"]:
                if table in filename:
                    table_names.add(table)
        
        self.assertIn("stocks", table_names)
        self.assertIn("fundamental_data", table_names)
        self.assertNotIn("news_articles", table_names)
    
    def test_export_invalid_format(self):
        """Test export with invalid format"""
        with self.assertRaises(ValueError):
            self.ops_manager.export_data("invalid_format")
    
    # ==================== PERFORMANCE OPERATIONS TESTS ====================
    
    def test_analyze_performance(self):
        """Test database performance analysis"""
        result = self.ops_manager.analyze_performance()
        
        # Verify analysis structure
        self.assertIn("database_size_bytes", result)
        self.assertIn("database_size_mb", result)
        self.assertIn("total_records", result)
        self.assertIn("table_statistics", result)
        self.assertIn("query_performance", result)
        self.assertIn("integrity_check", result)
        self.assertIn("recommendations", result)
        
        # Verify table statistics
        self.assertIn("stocks", result["table_statistics"])
        self.assertEqual(result["table_statistics"]["stocks"]["record_count"], 3)
        
        # Check fundamental_data table
        if "fundamental_data" in result["table_statistics"]:
            self.assertEqual(result["table_statistics"]["fundamental_data"]["record_count"], 3)
        
        # Verify integrity check
        self.assertEqual(result["integrity_check"], "ok")
        
        # Verify query performance tests
        self.assertIn("stock_count", result["query_performance"])
        self.assertGreaterEqual(result["query_performance"]["stock_count"], 0)
        
        # Verify recommendations exist
        self.assertIsInstance(result["recommendations"], list)
        self.assertGreater(len(result["recommendations"]), 0)
    
    def test_optimize_database(self):
        """Test database optimization"""
        result = self.ops_manager.optimize_database(vacuum=True, reindex=True)
        
        # Verify optimization structure
        self.assertIn("optimization_timestamp", result)
        self.assertIn("steps_performed", result)
        self.assertIn("pages_before", result)
        self.assertIn("pages_after", result)
        self.assertIn("space_saved_bytes", result)
        self.assertTrue(result["vacuum_performed"])
        self.assertTrue(result["reindex_performed"])
        
        # Verify optimization steps
        self.assertIn("VACUUM completed", result["steps_performed"])
        self.assertIn("REINDEX completed", result["steps_performed"])
    
    # ==================== CLEANUP OPERATIONS TESTS ====================
    
    def test_cleanup_old_data(self):
        """Test old data cleanup"""
        # Add old news article
        self.db_manager.connect()
        old_date = datetime.now() - timedelta(days=45)
        old_article = NewsArticle(
            symbol="AAPL",
            title="Old news",
            summary="Old summary",
            content="Old content",
            publisher="old_source",
            publish_date=old_date,
            url="http://old.com",
            sentiment_score=0.5,
            data_quality_score=0.5
        )
        self.db_manager.insert_news_articles([old_article])
        self.db_manager.connection.commit()
        self.db_manager.close()
        
        # Run cleanup with 30-day retention
        result = self.ops_manager.cleanup_old_data(retention_days=30)
        
        # Verify cleanup results
        self.assertIn("cleanup_timestamp", result)
        self.assertEqual(result["retention_days"], 30)
        self.assertIn("cleanup_results", result)
        self.assertIn("total_records_deleted", result)
        
        # Verify old news article was deleted
        self.assertGreaterEqual(result["cleanup_results"]["news_articles_deleted"], 1)
    
    # ==================== UTILITY METHODS TESTS ====================
    
    def test_list_backups(self):
        """Test listing available backups"""
        # Create multiple backups
        self.ops_manager.create_backup("backup1", compress=False)
        self.ops_manager.create_backup("backup2", compress=True)
        
        # List backups
        backups = self.ops_manager.list_backups()
        
        # Verify backup listing
        self.assertGreaterEqual(len(backups), 2)
        
        backup_names = [b["backup_name"] for b in backups]
        self.assertIn("backup1", backup_names)
        self.assertIn("backup2", backup_names)
        
        # Verify backup metadata
        for backup in backups:
            self.assertIn("file_size_bytes", backup)
            self.assertIn("compressed", backup)
            self.assertIn("file_path", backup)
    
    def test_get_storage_usage(self):
        """Test storage usage calculation"""
        # Create backup to generate storage usage
        self.ops_manager.create_backup("storage_test")
        
        usage = self.ops_manager.get_storage_usage()
        
        # Verify storage usage structure
        self.assertIn("database_size_bytes", usage)
        self.assertIn("backup_size_bytes", usage)
        self.assertIn("export_size_bytes", usage)
        self.assertIn("total_size_bytes", usage)
        self.assertIn("total_size_mb", usage)
        
        # Verify calculated totals
        expected_total = usage["database_size_bytes"] + usage["backup_size_bytes"] + usage["export_size_bytes"]
        self.assertEqual(usage["total_size_bytes"], expected_total)
        
        # Verify backup storage is recorded
        self.assertGreater(usage["backup_size_bytes"], 0)
    
    # ==================== ERROR HANDLING TESTS ====================
    
    def test_backup_database_connection_failure(self):
        """Test backup with database connection failure"""
        # Create manager with invalid database path
        invalid_db_manager = DatabaseManager()
        invalid_db_manager.db_path = "/invalid/path/database.db"
        
        ops_manager = DatabaseOperationsManager(invalid_db_manager)
        ops_manager.backup_dir = self.ops_manager.backup_dir
        
        with self.assertRaises(Exception):
            ops_manager.create_backup("fail_test")
    
    def test_export_database_connection_failure(self):
        """Test export with database connection failure"""
        # Create manager with invalid database path
        invalid_db_manager = DatabaseManager()
        invalid_db_manager.db_path = "/invalid/path/database.db"
        
        ops_manager = DatabaseOperationsManager(invalid_db_manager)
        ops_manager.export_dir = self.ops_manager.export_dir
        
        with self.assertRaises(Exception):
            ops_manager.export_data("csv")
    
    def test_corrupted_backup_verification(self):
        """Test verification of corrupted backup"""
        # Create valid backup first
        result = self.ops_manager.create_backup("corruption_test", compress=False)
        
        # Corrupt the backup file
        backup_file = self.ops_manager.backup_dir / "corruption_test.db"
        with open(backup_file, 'w') as f:
            f.write("corrupted data")
        
        # Try to restore corrupted backup
        with self.assertRaises(Exception):
            self.ops_manager.restore_backup("corruption_test", verify_before_restore=True)
    
    # ==================== INTEGRATION TESTS ====================
    
    def test_full_backup_restore_cycle(self):
        """Test complete backup and restore cycle"""
        # Create backup
        backup_result = self.ops_manager.create_backup("full_cycle_test")
        self.assertTrue(backup_result["integrity_verified"])
        
        # Modify database significantly
        self.db_manager.connect()
        cursor = self.db_manager.connection.cursor()
        cursor.execute("DROP TABLE stocks")
        self.db_manager.connection.commit()
        self.db_manager.close()
        
        # Restore backup
        restore_result = self.ops_manager.restore_backup("full_cycle_test")
        
        # Verify full restoration
        self.db_manager.connect()
        cursor = self.db_manager.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM stocks")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 3)
        self.db_manager.close()
    
    def test_export_after_optimization(self):
        """Test export functionality after database optimization"""
        # Optimize database
        opt_result = self.ops_manager.optimize_database()
        
        # Export data
        export_result = self.ops_manager.export_data("json")
        
        # Verify export still works correctly
        self.assertGreater(export_result["total_records"], 0)
        json_file = Path(export_result["files"][0])
        self.assertTrue(json_file.exists())
        
        with open(json_file, 'r') as f:
            data = json.load(f)
            self.assertEqual(len(data["stocks"]), 3)
    
    def test_performance_analysis_accuracy(self):
        """Test accuracy of performance analysis metrics"""
        # Get performance analysis
        perf_result = self.ops_manager.analyze_performance()
        
        # Verify record counts match actual database
        self.db_manager.connect()
        cursor = self.db_manager.connection.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM stocks")
        actual_stock_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM news_articles")
        actual_news_count = cursor.fetchone()[0]
        
        self.db_manager.close()
        
        # Compare with analysis results
        self.assertEqual(perf_result["table_statistics"]["stocks"]["record_count"], actual_stock_count)
        if "news_articles" in perf_result["table_statistics"]:
            self.assertEqual(perf_result["table_statistics"]["news_articles"]["record_count"], actual_news_count)


class TestDatabaseOperationsManagerProduction(unittest.TestCase):
    """Production-specific test scenarios"""
    
    def setUp(self):
        """Set up production-like test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, "production_test.db")
        
        # Create database with larger dataset
        self.db_manager = DatabaseManager()
        self.db_manager.db_path = self.test_db_path
        self.db_manager.connect()
        self.db_manager.create_tables()
        
        # Create production-scale sample data
        self._create_production_sample_data()
        self.db_manager.close()
        
        self.ops_manager = DatabaseOperationsManager(self.db_manager)
        self.ops_manager.backup_dir = Path(self.test_dir) / "backups"
        self.ops_manager.export_dir = Path(self.test_dir) / "exports"
        self.ops_manager.backup_dir.mkdir(exist_ok=True)
        self.ops_manager.export_dir.mkdir(exist_ok=True)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def _create_production_sample_data(self):
        """Create production-scale sample data"""
        # Insert 50 sample stocks (simulating partial S&P 500)
        sectors = ["Technology", "Healthcare", "Financials", "Consumer Discretionary", "Energy"]
        
        for i in range(50):
            symbol = f"TEST{i:03d}"
            name = f"Test Company {i}"
            sector = sectors[i % len(sectors)]
            industry = f"Test Industry {i % 10}"
            market_cap = 1000000000 * (i + 1)
            exchange = "NYSE" if i % 2 == 0 else "NASDAQ"
            
            self.db_manager.insert_stock(symbol, name, sector, industry, market_cap, exchange)
        
        # Insert fundamental data for each stock
        base_fundamentals = {
            'pe_ratio': 20.0,
            'ev_to_ebitda': 15.0,
            'peg_ratio': 1.2,
            'free_cash_flow': 5000000000,
            'market_cap': 100000000000,
            'total_revenue': 50000000000,
            'net_income': 10000000000,
            'total_assets': 75000000000,
            'total_debt': 25000000000,
            'shareholders_equity': 30000000000,
            'return_on_equity': 0.15,
            'debt_to_equity': 0.4,
            'current_ratio': 1.5,
            'revenue_growth': 0.10,
            'earnings_growth': 0.15,
            'data_source': 'production_test'
        }
        
        for i in range(50):
            symbol = f"TEST{i:03d}"
            # Vary the fundamentals slightly for each stock
            fundamentals = base_fundamentals.copy()
            fundamentals['pe_ratio'] *= (0.8 + (i % 5) * 0.1)
            fundamentals['market_cap'] *= (i + 1)
            
            self.db_manager.insert_fundamental_data(symbol, fundamentals)
        
        # Insert multiple news articles per stock
        all_news_articles = []
        for i in range(50):
            symbol = f"TEST{i:03d}"
            for j in range(5):  # 5 news articles per stock
                article = NewsArticle(
                    symbol=symbol,
                    title=f"News {j} for {symbol}",
                    summary=f"Summary {j} for {symbol}",
                    content=f"Content {j} for {symbol} " * 20,  # Larger content
                    publisher=f"source_{j % 3}",
                    publish_date=datetime.now() - timedelta(days=j),
                    url=f"http://test.com/{symbol}/{j}",
                    sentiment_score=0.1 + (j * 0.2),
                    data_quality_score=0.8
                )
                all_news_articles.append(article)
        
        if all_news_articles:
            self.db_manager.insert_news_articles(all_news_articles)
        
        self.db_manager.connection.commit()
    
    def test_production_scale_backup(self):
        """Test backup with production-scale data"""
        # Test both compressed and uncompressed backups
        uncompressed_result = self.ops_manager.create_backup("prod_uncompressed", compress=False)
        compressed_result = self.ops_manager.create_backup("prod_compressed", compress=True)
        
        # Verify both backups succeeded
        self.assertTrue(uncompressed_result["integrity_verified"])
        self.assertTrue(compressed_result["integrity_verified"])
        
        # Verify compression efficiency
        self.assertLess(compressed_result["file_size_bytes"], uncompressed_result["file_size_bytes"])
        
        # Verify record counts
        self.assertEqual(uncompressed_result["record_counts"]["stocks"], 50)
        self.assertEqual(uncompressed_result["record_counts"]["news_articles"], 250)  # 50 stocks * 5 articles
    
    def test_production_scale_export(self):
        """Test export with production-scale data"""
        # Test CSV export
        csv_result = self.ops_manager.export_data("csv")
        
        # Verify export completed
        self.assertGreater(csv_result["total_records"], 300)  # 50 stocks + 50 fundamentals + 250 news
        
        # Test JSON export
        json_result = self.ops_manager.export_data("json")
        
        # Verify JSON structure and content
        json_file = Path(json_result["files"][0])
        with open(json_file, 'r') as f:
            data = json.load(f)
            self.assertEqual(len(data["stocks"]), 50)
            self.assertEqual(len(data["news_articles"]), 250)
    
    def test_production_performance_analysis(self):
        """Test performance analysis with production-scale data"""
        result = self.ops_manager.analyze_performance()
        
        # Verify analysis handles larger dataset
        self.assertGreater(result["total_records"], 300)  # Should have substantial records
        self.assertGreater(result["database_size_bytes"], 100000)  # Should be substantial
        
        # Verify query performance is reasonable
        for query_name, duration in result["query_performance"].items():
            if duration > 0:  # Skip failed queries
                self.assertLess(duration, 5.0, f"Query {query_name} took too long: {duration}s")
    
    def test_production_cleanup_efficiency(self):
        """Test cleanup efficiency with production-scale data"""
        # Add old data across multiple dates
        self.db_manager.connect()
        old_articles = []
        for i in range(10):
            old_date = datetime.now() - timedelta(days=35 + i)
            article = NewsArticle(
                symbol="TEST000",
                title=f"Old news {i}",
                summary=f"Old summary {i}",
                content=f"Old content {i}",
                publisher="old_source",
                publish_date=old_date,
                url=f"http://old.com/{i}",
                sentiment_score=0.5,
                data_quality_score=0.5
            )
            old_articles.append(article)
        
        if old_articles:
            self.db_manager.insert_news_articles(old_articles)
        self.db_manager.connection.commit()
        self.db_manager.close()
        
        # Run cleanup
        result = self.ops_manager.cleanup_old_data(retention_days=30)
        
        # Verify cleanup efficiency
        self.assertGreaterEqual(result["cleanup_results"]["news_articles_deleted"], 10)
        self.assertGreater(result["total_records_deleted"], 0)


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2)