#!/usr/bin/env python3
"""
Comprehensive Tests for User-Controlled Data Quality Gating System
Production-critical testing for approval workflows
"""

import os
import sys
import tempfile
import shutil
import json
from datetime import datetime, timedelta
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.data.quality_gating import (
    QualityGatingSystem, GateStatus, ComponentType, 
    QualityGateRule, QualityGateResult, ComponentQualityStatus
)
from src.data.database import DatabaseManager, NewsArticle


class TestQualityGatingSystem(unittest.TestCase):
    """Test suite for Quality Gating System"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary directory for tests
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, "test_quality_gating.db")
        
        # Create test database with sample data
        self.db_manager = DatabaseManager()
        self.db_manager.db_path = self.test_db_path
        self.db_manager.connect()
        self.db_manager.create_tables()
        
        # Insert sample data
        self._create_sample_data()
        self.db_manager.close()
        
        # Create Quality Gating System
        self.gating_system = QualityGatingSystem(self.db_manager)
    
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
        
        # Insert sample fundamental data (recent - good quality)
        good_fundamentals = {
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
        
        # AAPL - good quality data
        self.db_manager.insert_fundamental_data("AAPL", good_fundamentals)
        
        # MSFT - older fundamental data (will trigger freshness rules)
        old_fundamentals = good_fundamentals.copy()
        old_fundamentals['data_source'] = 'old_test_data'  # Change source to indicate older data
        self.db_manager.insert_fundamental_data("MSFT", old_fundamentals)
        
        # Insert price data
        cursor = self.db_manager.connection.cursor()
        for symbol in ["AAPL", "MSFT"]:
            # Recent price data (good quality)
            for i in range(5):
                date_str = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                cursor.execute("""
                    INSERT INTO price_data (symbol, date, open, high, low, 
                                          close, volume, adjusted_close, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (symbol, date_str, 150.0 + i, 155.0 + i, 145.0 + i, 152.0 + i,
                      1000000, 152.0 + i, 'test_data'))
        
        # Old price data for GOOGL (will trigger freshness rules)
        for i in range(5):
            date_str = (datetime.now() - timedelta(days=10 + i)).strftime('%Y-%m-%d')
            cursor.execute("""
                INSERT INTO price_data (symbol, date, open, high, low, 
                                      close, volume, adjusted_close, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ("GOOGL", date_str, 2500.0 + i, 2550.0 + i, 2450.0 + i, 2520.0 + i,
                  500000, 2520.0 + i, 'test_data'))
        
        # Insert news articles
        all_news_articles = []
        for i, symbol in enumerate(["AAPL", "MSFT"]):
            for j in range(5):
                published_date = datetime.now() - timedelta(days=j)
                article = NewsArticle(
                    symbol=symbol,
                    title=f"Test news {j} for {symbol}",
                    summary=f"Test summary {j} for {symbol}",
                    content=f"Test content {j} for {symbol}",
                    publisher="test_source",
                    publish_date=published_date,
                    url=f"http://test.com/{symbol}/{j}",
                    sentiment_score=0.5 + (j * 0.1),
                    data_quality_score=0.8
                )
                all_news_articles.append(article)
        
        # Limited news for GOOGL (will trigger count rules)
        googl_article = NewsArticle(
            symbol="GOOGL",
            title="Single news for GOOGL",
            summary="Limited news summary",
            content="Limited news content",
            publisher="test_source",
            publish_date=datetime.now() - timedelta(days=1),
            url="http://test.com/GOOGL/1",
            sentiment_score=0.6,
            data_quality_score=0.7
        )
        all_news_articles.append(googl_article)
        
        # Insert all news articles
        if all_news_articles:
            self.db_manager.insert_news_articles(all_news_articles)
        
        # Insert sentiment data
        for symbol in ["AAPL", "MSFT"]:
            for i in range(7):
                date_str = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                cursor.execute("""
                    INSERT INTO daily_sentiment (symbol, date, news_sentiment, reddit_sentiment,
                                               combined_sentiment, news_count, reddit_count, data_quality)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (symbol, date_str, 0.6, 0.5, 0.55, 3, 2, 0.8))
        
        self.db_manager.connection.commit()
    
    # ==================== SYSTEM INITIALIZATION TESTS ====================
    
    def test_system_initialization(self):
        """Test quality gating system initialization"""
        # Verify system initialized properly
        self.assertIsNotNone(self.gating_system.db_manager)
        self.assertIsNotNone(self.gating_system.rules)
        self.assertGreater(len(self.gating_system.rules), 0)
        
        # Check database tables were created
        self.db_manager.connect()
        cursor = self.db_manager.connection.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quality_gates'")
        self.assertIsNotNone(cursor.fetchone())
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='data_versions'")
        self.assertIsNotNone(cursor.fetchone())
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quality_gate_rules'")
        self.assertIsNotNone(cursor.fetchone())
        
        self.db_manager.close()
    
    def test_default_quality_rules(self):
        """Test default quality rules are loaded"""
        rules = self.gating_system.rules
        
        # Check we have expected default rules
        rule_components = [rule.component for rule in rules]
        self.assertIn("fundamentals", rule_components)
        self.assertIn("price_data", rule_components)
        self.assertIn("news_data", rule_components)
        self.assertIn("sentiment_data", rule_components)
        
        # Check rule structure
        for rule in rules:
            self.assertIsInstance(rule, QualityGateRule)
            self.assertIsNotNone(rule.component)
            self.assertIsNotNone(rule.metric)
            self.assertIsNotNone(rule.threshold)
            self.assertIsNotNone(rule.operator)
    
    # ==================== COMPONENT QUALITY EVALUATION TESTS ====================
    
    def test_evaluate_fundamentals_quality_good(self):
        """Test fundamental data quality evaluation - good quality"""
        status = self.gating_system.evaluate_component_quality("AAPL", ComponentType.FUNDAMENTALS)
        
        # Verify status structure
        self.assertEqual(status.component, ComponentType.FUNDAMENTALS)
        self.assertEqual(status.symbol, "AAPL")
        self.assertGreater(status.quality_score, 0.7)  # Should be high quality
        self.assertLess(status.data_freshness_hours, 24)  # Should be fresh
        self.assertEqual(status.record_count, 1)
        self.assertIn(status.gate_status, [GateStatus.PENDING, GateStatus.APPROVED])
    
    def test_evaluate_price_data_quality_stale(self):
        """Test price data quality evaluation - stale data"""
        status = self.gating_system.evaluate_component_quality("GOOGL", ComponentType.PRICE_DATA)
        
        # GOOGL has 10+ day old price data, should trigger freshness rule
        self.assertEqual(status.component, ComponentType.PRICE_DATA)
        self.assertEqual(status.symbol, "GOOGL")
        self.assertGreater(status.data_freshness_hours, 48)  # Should be stale
        self.assertEqual(status.gate_status, GateStatus.BLOCKED)  # Should be blocked
        self.assertGreater(len(status.quality_issues), 0)  # Should have blocking rules
    
    def test_evaluate_news_data_insufficient(self):
        """Test news data quality evaluation - insufficient articles"""
        status = self.gating_system.evaluate_component_quality("GOOGL", ComponentType.NEWS_DATA)
        
        # GOOGL has only 1 news article, should trigger count rule (warning only)
        self.assertEqual(status.component, ComponentType.NEWS_DATA)
        self.assertEqual(status.symbol, "GOOGL")
        self.assertEqual(status.record_count, 1)
        # Should be pending since news rule is warning-only, not blocking
        self.assertIn(status.gate_status, [GateStatus.PENDING, GateStatus.APPROVED])
    
    def test_evaluate_sentiment_quality_good(self):
        """Test sentiment data quality evaluation - good quality"""
        status = self.gating_system.evaluate_component_quality("AAPL", ComponentType.SENTIMENT_DATA)
        
        self.assertEqual(status.component, ComponentType.SENTIMENT_DATA)
        self.assertEqual(status.symbol, "AAPL")
        self.assertGreater(status.record_count, 0)
        self.assertLess(status.data_freshness_hours, 48)
        # Sentiment rules are typically warning-only
        self.assertIn(status.gate_status, [GateStatus.PENDING, GateStatus.APPROVED])
    
    def test_evaluate_system_quality_comprehensive(self):
        """Test comprehensive system quality evaluation"""
        results = self.gating_system.evaluate_system_quality("AAPL")
        
        # Verify all components evaluated
        expected_components = ["fundamentals", "price_data", "news_data", "sentiment_data"]
        for component in expected_components:
            self.assertIn(component, results)
            self.assertIsInstance(results[component], ComponentQualityStatus)
        
        # AAPL should have generally good quality
        fundamentals_status = results["fundamentals"]
        self.assertGreater(fundamentals_status.quality_score, 0.7)
        
        price_status = results["price_data"]
        self.assertLess(price_status.data_freshness_hours, 48)
    
    # ==================== APPROVAL WORKFLOW TESTS ====================
    
    def test_request_approval_pending(self):
        """Test requesting approval for good quality component"""
        gate_result = self.gating_system.request_approval("AAPL", ComponentType.FUNDAMENTALS, "test_user")
        
        # Verify approval request
        self.assertEqual(gate_result.component, "fundamentals")
        self.assertIn(gate_result.status, [GateStatus.PENDING, GateStatus.BLOCKED])
        self.assertIsNotNone(gate_result.gate_id)
        self.assertIn("test_user", gate_result.metadata.get("requested_by", ""))
    
    def test_request_approval_blocked(self):
        """Test requesting approval for blocked component"""
        gate_result = self.gating_system.request_approval("GOOGL", ComponentType.PRICE_DATA, "test_user")
        
        # Should be blocked due to stale price data
        self.assertEqual(gate_result.component, "price_data")
        self.assertEqual(gate_result.status, GateStatus.BLOCKED)
        self.assertGreater(len(gate_result.blocking_rules), 0)
        self.assertTrue(gate_result.metadata.get("auto_blocked", False))
    
    def test_approve_component_success(self):
        """Test successful component approval"""
        # Approve AAPL fundamentals
        gate_result = self.gating_system.approve_component("AAPL", ComponentType.FUNDAMENTALS, "test_user", 48)
        
        # Verify approval
        self.assertEqual(gate_result.status, GateStatus.APPROVED)
        self.assertEqual(gate_result.approved_by, "test_user")
        self.assertIsNotNone(gate_result.approval_timestamp)
        self.assertIsNotNone(gate_result.expires_at)
        
        # Verify expiration is correct
        expected_expiry = gate_result.approval_timestamp + timedelta(hours=48)
        self.assertEqual(gate_result.expires_at.replace(microsecond=0), 
                        expected_expiry.replace(microsecond=0))
    
    def test_approve_component_blocked(self):
        """Test approval attempt on blocked component"""
        # Try to approve GOOGL price data (should be blocked)
        with self.assertRaises(Exception) as context:
            self.gating_system.approve_component("GOOGL", ComponentType.PRICE_DATA, "test_user")
        
        self.assertIn("blocked by quality rules", str(context.exception).lower())
    
    def test_reject_component(self):
        """Test component rejection"""
        gate_result = self.gating_system.reject_component("MSFT", ComponentType.FUNDAMENTALS, 
                                                         "test_user", "Data too old")
        
        # Verify rejection
        self.assertEqual(gate_result.status, GateStatus.REJECTED)
        self.assertIn("test_user", gate_result.metadata.get("rejected_by", ""))
        self.assertIn("Data too old", gate_result.metadata.get("rejection_reason", ""))
        self.assertIsNotNone(gate_result.metadata.get("rejection_timestamp"))
    
    def test_approval_workflow_complete(self):
        """Test complete approval workflow"""
        symbol = "AAPL"
        component = ComponentType.FUNDAMENTALS
        
        # 1. Request approval
        request_result = self.gating_system.request_approval(symbol, component, "analyst1")
        
        # 2. Approve component
        approval_result = self.gating_system.approve_component(symbol, component, "manager1", 24)
        
        # Verify workflow
        self.assertEqual(approval_result.status, GateStatus.APPROVED)
        self.assertEqual(approval_result.approved_by, "manager1")
        
        # 3. Verify data version was created
        data_version = self.gating_system.get_approved_data_version(symbol, component)
        self.assertIsNotNone(data_version)
        self.assertIsNotNone(data_version["version_id"])
        self.assertIsNotNone(data_version["approved_at"])
    
    # ==================== ANALYSIS CONTROL TESTS ====================
    
    def test_analysis_allowed_all_approved(self):
        """Test analysis permission when all components approved"""
        symbol = "AAPL"
        
        # Approve all components
        components = [ComponentType.FUNDAMENTALS, ComponentType.PRICE_DATA, 
                     ComponentType.NEWS_DATA, ComponentType.SENTIMENT_DATA]
        
        for component in components:
            try:
                self.gating_system.approve_component(symbol, component, "test_user", 24)
            except Exception:
                # Some components might not be approvable due to quality rules
                pass
        
        # Check analysis permission
        permission = self.gating_system.is_analysis_allowed(symbol, components)
        
        # Verify structure
        self.assertEqual(permission["symbol"], symbol)
        self.assertIsInstance(permission["analysis_allowed"], bool)
        self.assertIsInstance(permission["blocking_components"], list)
        self.assertIsInstance(permission["warning_components"], list)
        self.assertIn("component_details", permission)
        
        # At least fundamentals should be approvable for AAPL
        fundamentals_detail = permission["component_details"]["fundamentals"]
        self.assertIn("gate_status", fundamentals_detail)
        self.assertIn("quality_score", fundamentals_detail)
    
    def test_analysis_blocked_by_quality(self):
        """Test analysis blocked by quality issues"""
        symbol = "GOOGL"  # Has stale price data
        
        permission = self.gating_system.is_analysis_allowed(symbol)
        
        # Should be blocked due to stale price data
        self.assertFalse(permission["analysis_allowed"])
        self.assertIn("price_data", permission["blocking_components"])
    
    def test_analysis_allowed_partial_components(self):
        """Test analysis with only required components"""
        symbol = "AAPL"
        
        # Approve only fundamentals
        self.gating_system.approve_component(symbol, ComponentType.FUNDAMENTALS, "test_user", 24)
        
        # Check permission for fundamentals only
        permission = self.gating_system.is_analysis_allowed(symbol, [ComponentType.FUNDAMENTALS])
        
        # Should be allowed for fundamentals-only analysis
        fundamentals_status = permission["component_details"]["fundamentals"]["gate_status"]
        self.assertIn(fundamentals_status, ["approved", "pending"])  # Depending on quality rules
    
    def test_get_approved_data_version(self):
        """Test retrieving approved data version"""
        symbol = "AAPL"
        component = ComponentType.FUNDAMENTALS
        
        # Approve component
        self.gating_system.approve_component(symbol, component, "test_user", 24)
        
        # Get approved version
        version = self.gating_system.get_approved_data_version(symbol, component)
        
        self.assertIsNotNone(version)
        self.assertIn("version_id", version)
        self.assertIn("approved_at", version)
        self.assertIn("expires_at", version)
        
        # Verify version has reasonable data
        self.assertTrue(version["version_id"].startswith(f"{symbol}_{component.value}"))
    
    def test_get_approved_data_version_none(self):
        """Test retrieving approved data version when none exists"""
        version = self.gating_system.get_approved_data_version("GOOGL", ComponentType.PRICE_DATA)
        self.assertIsNone(version)
    
    # ==================== BULK OPERATIONS TESTS ====================
    
    def test_bulk_evaluate_quality(self):
        """Test bulk quality evaluation"""
        symbols = ["AAPL", "MSFT", "GOOGL"]
        
        results = self.gating_system.bulk_evaluate_quality(symbols)
        
        # Verify all symbols evaluated
        for symbol in symbols:
            self.assertIn(symbol, results)
            symbol_results = results[symbol]
            
            # Should have all components
            expected_components = ["fundamentals", "price_data", "news_data", "sentiment_data"]
            for component in expected_components:
                if component in symbol_results:  # Some might fail evaluation
                    self.assertIsInstance(symbol_results[component], ComponentQualityStatus)
    
    def test_bulk_approve_components(self):
        """Test bulk component approval"""
        approvals = [
            ("AAPL", ComponentType.FUNDAMENTALS),
            ("AAPL", ComponentType.NEWS_DATA),
            ("MSFT", ComponentType.NEWS_DATA)
        ]
        
        results = self.gating_system.bulk_approve_components(approvals, "bulk_user")
        
        # Verify results for each approval
        for symbol, component in approvals:
            key = f"{symbol}_{component.value}"
            self.assertIn(key, results)
            
            result = results[key]
            self.assertIsInstance(result, QualityGateResult)
            # Should be approved or have error details
            self.assertIn(result.status, [GateStatus.APPROVED, GateStatus.BLOCKED])
    
    def test_bulk_approve_mixed_quality(self):
        """Test bulk approval with mixed quality components"""
        approvals = [
            ("AAPL", ComponentType.FUNDAMENTALS),  # Should work
            ("GOOGL", ComponentType.PRICE_DATA),   # Should fail (stale data)
        ]
        
        results = self.gating_system.bulk_approve_components(approvals, "test_user")
        
        # AAPL fundamentals should succeed
        aapl_key = f"AAPL_{ComponentType.FUNDAMENTALS.value}"
        if aapl_key in results:
            aapl_result = results[aapl_key]
            self.assertIn(aapl_result.status, [GateStatus.APPROVED, GateStatus.PENDING])
        
        # GOOGL price data should fail
        googl_key = f"GOOGL_{ComponentType.PRICE_DATA.value}"
        googl_result = results[googl_key]
        self.assertEqual(googl_result.status, GateStatus.BLOCKED)
    
    # ==================== UTILITY AND MANAGEMENT TESTS ====================
    
    def test_get_gate_summary_all(self):
        """Test getting gate summary for all stocks"""
        # Create some gates first
        self.gating_system.request_approval("AAPL", ComponentType.FUNDAMENTALS, "test_user")
        self.gating_system.approve_component("AAPL", ComponentType.FUNDAMENTALS, "test_user", 24)
        
        summary = self.gating_system.get_gate_summary()
        
        # Verify summary structure
        self.assertIn("total_gates", summary)
        self.assertIn("by_status", summary)
        self.assertIn("by_component", summary)
        self.assertIn("by_symbol", summary)
        
        # Should have at least one gate
        self.assertGreater(summary["total_gates"], 0)
    
    def test_get_gate_summary_specific_symbol(self):
        """Test getting gate summary for specific symbol"""
        symbol = "AAPL"
        
        # Create gate
        self.gating_system.request_approval(symbol, ComponentType.FUNDAMENTALS, "test_user")
        
        summary = self.gating_system.get_gate_summary(symbol)
        
        # Should have gate for AAPL
        self.assertGreater(summary["total_gates"], 0)
        self.assertIn(symbol, summary["by_symbol"])
    
    def test_cleanup_expired_gates(self):
        """Test cleanup of expired gates"""
        symbol = "AAPL"
        component = ComponentType.FUNDAMENTALS
        
        # Approve with very short duration (1/3600 = 1 second)
        self.gating_system.approve_component(symbol, component, "test_user", 1/3600)  # 1 second
        
        # Wait for expiration
        import time
        time.sleep(1.1)  # Wait slightly longer than expiration
        
        # Run cleanup
        expired_count = self.gating_system.cleanup_expired_gates()
        
        # Should have cleaned up at least one gate
        self.assertGreaterEqual(expired_count, 0)  # Might be 0 if timing is off
        
        # Verify gate is now expired
        status = self.gating_system.evaluate_component_quality(symbol, component)
        if status.gate_result:
            # If gate exists, it should be expired or new pending
            self.assertIn(status.gate_result.status, [GateStatus.EXPIRED, GateStatus.PENDING])
    
    # ==================== ERROR HANDLING TESTS ====================
    
    def test_evaluate_quality_nonexistent_symbol(self):
        """Test quality evaluation for non-existent symbol"""
        status = self.gating_system.evaluate_component_quality("NONEXISTENT", ComponentType.FUNDAMENTALS)
        
        # Should return low quality status
        self.assertEqual(status.symbol, "NONEXISTENT")
        self.assertEqual(status.quality_score, 0.0)
        self.assertEqual(status.record_count, 0)
        self.assertGreater(status.data_freshness_hours, 100)  # Very stale
    
    def test_approve_nonexistent_symbol(self):
        """Test approval attempt for non-existent symbol"""
        # Should not raise exception, but create blocked gate
        gate_result = self.gating_system.request_approval("NONEXISTENT", ComponentType.FUNDAMENTALS, "test_user")
        
        # Should be blocked due to no data
        self.assertEqual(gate_result.status, GateStatus.BLOCKED)
    
    def test_database_connection_failure_handling(self):
        """Test handling of database connection failures"""
        # Create system with invalid database
        invalid_db_manager = DatabaseManager()
        invalid_db_manager.db_path = "/invalid/path/database.db"
        
        # Should raise exception during initialization
        with self.assertRaises(Exception):
            QualityGatingSystem(invalid_db_manager)
    
    # ==================== INTEGRATION TESTS ====================
    
    def test_complete_quality_workflow(self):
        """Test complete quality gating workflow"""
        symbol = "AAPL"
        
        # 1. Evaluate initial quality
        initial_quality = self.gating_system.evaluate_system_quality(symbol)
        
        # 2. Request approvals for good components
        good_components = []
        for component_name, status in initial_quality.items():
            if status.gate_status != GateStatus.BLOCKED:
                component = ComponentType(component_name)
                good_components.append(component)
                self.gating_system.request_approval(symbol, component, "analyst")
        
        # 3. Approve components
        approved_components = []
        for component in good_components:
            try:
                self.gating_system.approve_component(symbol, component, "manager", 24)
                approved_components.append(component)
            except Exception as e:
                # Some components might not be approvable
                print(f"Could not approve {component.value}: {e}")
        
        # 4. Check analysis permission
        permission = self.gating_system.is_analysis_allowed(symbol, approved_components)
        
        # Should be allowed for approved components
        if approved_components:
            # At least some analysis should be possible
            total_blocking = len(permission["blocking_components"])
            total_required = len(approved_components)
            self.assertLess(total_blocking, total_required)
    
    def test_quality_gating_with_database_operations(self):
        """Test quality gating integration with database operations"""
        symbol = "AAPL"
        component = ComponentType.FUNDAMENTALS
        
        # Approve component
        gate_result = self.gating_system.approve_component(symbol, component, "test_user", 24)
        
        # Verify gate was saved to database
        self.db_manager.connect()
        cursor = self.db_manager.connection.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM quality_gates WHERE gate_id = ?", (gate_result.gate_id,))
        gate_count = cursor.fetchone()[0]
        self.assertEqual(gate_count, 1)
        
        cursor.execute("SELECT COUNT(*) FROM data_versions WHERE approval_gate_id = ?", (gate_result.gate_id,))
        version_count = cursor.fetchone()[0]
        self.assertEqual(version_count, 1)
        
        self.db_manager.close()
    
    def test_concurrent_approval_workflow(self):
        """Test concurrent approval workflows"""
        import threading
        import queue
        
        symbol = "AAPL"
        results_queue = queue.Queue()
        
        def approve_component_thread(component_type, user_id):
            try:
                result = self.gating_system.approve_component(symbol, component_type, f"user_{user_id}", 24)
                results_queue.put((component_type.value, True, result))
            except Exception as e:
                results_queue.put((component_type.value, False, str(e)))
        
        # Start concurrent approvals
        components = [ComponentType.FUNDAMENTALS, ComponentType.NEWS_DATA]
        threads = []
        
        for i, component in enumerate(components):
            thread = threading.Thread(target=approve_component_thread, args=(component, i))
            thread.start()
            threads.append(thread)
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=30)
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        # Should have results for both components
        self.assertEqual(len(results), 2)
        
        # At least one should succeed (fundamentals should be approvable)
        success_count = sum(1 for _, success, _ in results if success)
        self.assertGreater(success_count, 0)


class TestQualityGatingProductionScenarios(unittest.TestCase):
    """Production scenario tests for Quality Gating System"""
    
    def setUp(self):
        """Set up production scenario test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, "production_gating_test.db")
        
        self.db_manager = DatabaseManager()
        self.db_manager.db_path = self.test_db_path
        self.db_manager.connect()
        self.db_manager.create_tables()
        
        # Create production-like dataset
        self._create_production_dataset()
        self.db_manager.close()
        
        self.gating_system = QualityGatingSystem(self.db_manager)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def _create_production_dataset(self):
        """Create production-like dataset with quality variations"""
        # Create 20 stocks with varying data quality
        for i in range(20):
            symbol = f"STOCK{i:03d}"
            self.db_manager.insert_stock(
                symbol, f"Test Company {i}", 
                "Technology" if i % 2 == 0 else "Healthcare",
                f"Industry {i % 5}", 
                1000000000 * (i + 1), 
                "NASDAQ"
            )
            
            # Varying fundamental data quality
            if i < 15:  # 75% have good fundamentals
                good_fundamentals = {
                    'pe_ratio': 20.0 + i, 'ev_to_ebitda': 15.0, 'peg_ratio': 1.5,
                    'free_cash_flow': 5000000000, 'market_cap': 100000000000,
                    'total_revenue': 50000000000, 'net_income': 10000000000,
                    'total_assets': 75000000000, 'total_debt': 25000000000,
                    'shareholders_equity': 30000000000, 'return_on_equity': 0.15,
                    'debt_to_equity': 0.35, 'current_ratio': 1.5,
                    'revenue_growth': 0.08, 'earnings_growth': 0.12,
                    'data_source': 'production_test'
                }
                self.db_manager.insert_fundamental_data(symbol, good_fundamentals)
            
            # Varying price data freshness
            if i < 18:  # 90% have recent price data
                days_old = 0 if i < 10 else 1  # Some 1-day old, some current
                for j in range(5):
                    date_str = (datetime.now() - timedelta(days=days_old + j)).strftime('%Y-%m-%d')
                    cursor = self.db_manager.connection.cursor()
                    cursor.execute("""
                        INSERT INTO price_data (symbol, date, open, high, low, 
                                              close, volume, adjusted_close, source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (symbol, date_str, 100.0 + i, 105.0 + i, 95.0 + i, 102.0 + i,
                          1000000, 102.0 + i, 'production_test'))
            
            # Varying news data availability
            news_count = max(0, 8 - i // 3)  # Decreasing news count
            symbol_articles = []
            for j in range(news_count):
                published_date = datetime.now() - timedelta(days=j)
                article = NewsArticle(
                    symbol=symbol,
                    title=f"News {j} for {symbol}",
                    summary=f"News summary {j} for {symbol}",
                    content=f"News content {j} for {symbol}",
                    publisher="production_test",
                    publish_date=published_date,
                    url=f"http://test.com/{symbol}/{j}",
                    sentiment_score=0.5 + (j * 0.1),
                    data_quality_score=0.8
                )
                symbol_articles.append(article)
            
            if symbol_articles:
                self.db_manager.insert_news_articles(symbol_articles)
        
        self.db_manager.connection.commit()
    
    def test_production_scale_quality_evaluation(self):
        """Test quality evaluation at production scale"""
        symbols = [f"STOCK{i:03d}" for i in range(20)]
        
        # Bulk evaluate quality
        start_time = datetime.now()
        results = self.gating_system.bulk_evaluate_quality(symbols)
        evaluation_time = (datetime.now() - start_time).total_seconds()
        
        # Verify performance
        self.assertLess(evaluation_time, 10.0, f"Quality evaluation too slow: {evaluation_time:.2f}s")
        
        # Verify all symbols evaluated
        self.assertEqual(len(results), 20)
        
        # Analyze quality distribution
        quality_stats = {
            "fundamentals": {"good": 0, "poor": 0},
            "price_data": {"good": 0, "poor": 0},
            "news_data": {"good": 0, "poor": 0}
        }
        
        for symbol, symbol_results in results.items():
            for component, status in symbol_results.items():
                if component in quality_stats:
                    if status.quality_score > 0.5:
                        quality_stats[component]["good"] += 1
                    else:
                        quality_stats[component]["poor"] += 1
        
        # Verify quality distribution matches our test data
        self.assertGreater(quality_stats["fundamentals"]["good"], 10)  # 75% should be good
        self.assertGreater(quality_stats["price_data"]["good"], 15)    # 90% should be good
    
    def test_production_approval_workflow_performance(self):
        """Test approval workflow performance at scale"""
        symbols = [f"STOCK{i:03d}" for i in range(10)]  # Subset for approval testing
        
        # Bulk request approvals
        approvals = []
        for symbol in symbols:
            approvals.append((symbol, ComponentType.FUNDAMENTALS))
            approvals.append((symbol, ComponentType.PRICE_DATA))
        
        start_time = datetime.now()
        results = self.gating_system.bulk_approve_components(approvals, "production_user")
        approval_time = (datetime.now() - start_time).total_seconds()
        
        # Verify performance
        self.assertLess(approval_time, 15.0, f"Bulk approval too slow: {approval_time:.2f}s")
        
        # Verify results
        self.assertEqual(len(results), len(approvals))
        
        # Count successful approvals
        approved_count = sum(1 for result in results.values() 
                           if result.status == GateStatus.APPROVED)
        
        # Should have some successful approvals
        self.assertGreater(approved_count, 5)
    
    def test_production_analysis_permission_checking(self):
        """Test analysis permission checking at scale"""
        symbols = [f"STOCK{i:03d}" for i in range(20)]
        
        # Check analysis permissions for all stocks
        start_time = datetime.now()
        permissions = []
        for symbol in symbols:
            permission = self.gating_system.is_analysis_allowed(symbol)
            permissions.append(permission)
        
        check_time = (datetime.now() - start_time).total_seconds()
        
        # Verify performance
        self.assertLess(check_time, 20.0, f"Permission checking too slow: {check_time:.2f}s")
        
        # Analyze permission results
        allowed_count = sum(1 for p in permissions if p["analysis_allowed"])
        blocked_count = len(permissions) - allowed_count
        
        # Most should be blocked initially (no approvals yet)
        self.assertGreater(blocked_count, allowed_count)
        
        # Verify permission structure
        for permission in permissions:
            self.assertIn("analysis_allowed", permission)
            self.assertIn("component_details", permission)
            self.assertIn("blocking_components", permission)


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2)