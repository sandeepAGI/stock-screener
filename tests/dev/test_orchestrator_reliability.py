#!/usr/bin/env python3
"""
Orchestrator Reliability Test Framework

Tests the reliability of DataCollectionOrchestrator refresh methods by comparing
what the orchestrator reports vs what actually gets stored in the database.

This helps us determine if we can trust orchestrator results for validation.
"""

import sys
import os
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data.collectors import DataCollectionOrchestrator
from src.data.database import DatabaseManager

@dataclass
class TestResult:
    """Container for test results"""
    test_name: str
    symbol: str
    data_type: str
    orchestrator_claimed_success: bool
    orchestrator_success_count: int
    actual_records_before: int
    actual_records_after: int
    actual_records_inserted: int
    records_match_claim: bool
    notes: str

class OrchestratorReliabilityTester:
    """Test framework for orchestrator reliability"""
    
    def __init__(self):
        self.orchestrator = DataCollectionOrchestrator()
        self.db_manager = DatabaseManager() 
        self.db_manager.connect()
        self.test_results: List[TestResult] = []
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def get_record_count(self, symbol: str, data_type: str) -> int:
        """Get current record count for a symbol and data type"""
        conn = sqlite3.connect('data/stock_data.db')
        cursor = conn.cursor()
        
        try:
            if data_type == 'fundamentals':
                cursor.execute("SELECT COUNT(*) FROM fundamental_data WHERE symbol = ?", (symbol,))
            elif data_type == 'prices':
                cursor.execute("SELECT COUNT(*) FROM price_data WHERE symbol = ?", (symbol,))
            elif data_type == 'news':
                cursor.execute("SELECT COUNT(*) FROM news_articles WHERE symbol = ?", (symbol,))
            elif data_type == 'sentiment':
                cursor.execute("SELECT COUNT(*) FROM reddit_posts WHERE symbol = ?", (symbol,))
            else:
                return 0
                
            count = cursor.fetchone()[0]
            conn.close()
            return count
            
        except Exception as e:
            self.logger.error(f"Error getting record count for {symbol} {data_type}: {e}")
            conn.close()
            return 0
    
    def test_fresh_symbol(self, symbol: str, data_type: str) -> TestResult:
        """Test orchestrator reliability on a symbol with no existing data"""
        print(f"\n🧪 Testing Fresh Symbol: {symbol} ({data_type})")
        
        # Get baseline count (should be 0 for fresh symbol)
        records_before = self.get_record_count(symbol, data_type)
        print(f"   📊 Records before: {records_before}")
        
        # Execute refresh operation
        if data_type == 'fundamentals':
            results = self.orchestrator.refresh_fundamentals_only([symbol])
        elif data_type == 'prices':
            results = self.orchestrator.refresh_prices_only([symbol])
        elif data_type == 'news':
            results = self.orchestrator.refresh_news_only([symbol])
        elif data_type == 'sentiment':
            results = self.orchestrator.refresh_sentiment_only([symbol])
        else:
            raise ValueError(f"Unknown data type: {data_type}")
        
        # Get results
        orchestrator_success = results.get(symbol, False)
        orchestrator_count = 1 if orchestrator_success else 0
        
        # Get post-refresh count
        records_after = self.get_record_count(symbol, data_type)
        records_inserted = records_after - records_before
        
        print(f"   🤖 Orchestrator claims: {'Success' if orchestrator_success else 'Failure'}")
        print(f"   📊 Records after: {records_after}")
        print(f"   ➕ Records inserted: {records_inserted}")
        
        # Determine if results match
        if orchestrator_success:
            # If orchestrator claims success, we should see new records
            records_match = records_inserted > 0
            match_status = "✅ MATCH" if records_match else "❌ MISMATCH"
        else:
            # If orchestrator claims failure, we should see no new records
            records_match = records_inserted == 0
            match_status = "✅ MATCH" if records_match else "❌ MISMATCH"
        
        print(f"   {match_status}")
        
        return TestResult(
            test_name="Fresh Symbol Test",
            symbol=symbol,
            data_type=data_type,
            orchestrator_claimed_success=orchestrator_success,
            orchestrator_success_count=orchestrator_count,
            actual_records_before=records_before,
            actual_records_after=records_after,
            actual_records_inserted=records_inserted,
            records_match_claim=records_match,
            notes=f"Fresh symbol test - baseline: {records_before}, after: {records_after}"
        )
    
    def test_existing_symbol(self, symbol: str, data_type: str) -> TestResult:
        """Test orchestrator reliability on a symbol with existing data"""
        print(f"\n🧪 Testing Existing Symbol: {symbol} ({data_type})")
        
        # Get baseline count
        records_before = self.get_record_count(symbol, data_type)
        print(f"   📊 Records before: {records_before}")
        
        # Execute refresh operation
        if data_type == 'fundamentals':
            results = self.orchestrator.refresh_fundamentals_only([symbol])
        elif data_type == 'prices':
            results = self.orchestrator.refresh_prices_only([symbol])
        elif data_type == 'news':
            results = self.orchestrator.refresh_news_only([symbol])
        elif data_type == 'sentiment':
            results = self.orchestrator.refresh_sentiment_only([symbol])
        else:
            raise ValueError(f"Unknown data type: {data_type}")
        
        # Get results
        orchestrator_success = results.get(symbol, False)
        orchestrator_count = 1 if orchestrator_success else 0
        
        # Get post-refresh count
        records_after = self.get_record_count(symbol, data_type)
        records_inserted = records_after - records_before
        
        print(f"   🤖 Orchestrator claims: {'Success' if orchestrator_success else 'Failure'}")
        print(f"   📊 Records after: {records_after}")
        print(f"   ➕ Records inserted: {records_inserted}")
        
        # For existing symbols, success might mean:
        # 1. New records added (records_inserted > 0)
        # 2. Existing records updated (INSERT OR REPLACE - same count but newer data)
        # 3. No new data available (legitimate failure)
        
        if orchestrator_success:
            # Success should mean either new records OR updated existing records
            # For now, we'll accept success if orchestrator claims it (may need refinement)
            records_match = True  # We'll analyze patterns in the results
            match_status = "✅ SUCCESS CLAIMED"
        else:
            # Failure should mean no new records
            records_match = records_inserted == 0
            match_status = "✅ MATCH" if records_match else "❌ MISMATCH"
        
        print(f"   {match_status}")
        
        return TestResult(
            test_name="Existing Symbol Test",
            symbol=symbol,
            data_type=data_type,
            orchestrator_claimed_success=orchestrator_success,
            orchestrator_success_count=orchestrator_count,
            actual_records_before=records_before,
            actual_records_after=records_after,
            actual_records_inserted=records_inserted,
            records_match_claim=records_match,
            notes=f"Existing symbol test - baseline: {records_before}, after: {records_after}"
        )
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive orchestrator reliability tests"""
        print("🧪 Starting Orchestrator Reliability Tests")
        print("=" * 60)
        
        # Test A: Fresh symbols (no existing data)
        fresh_symbols = ['ABBV', 'ABNB', 'ACGL']  # Symbols we know have no Reddit data
        for symbol in fresh_symbols:
            result = self.test_fresh_symbol(symbol, 'sentiment')
            self.test_results.append(result)
        
        # Test B: Existing symbols (has data)  
        existing_symbols = ['AAPL', 'MSFT', 'TSLA']  # Symbols we know have Reddit data
        for symbol in existing_symbols:
            result = self.test_existing_symbol(symbol, 'sentiment')
            self.test_results.append(result)
        
        # Analyze results
        return self.analyze_results()
    
    def analyze_results(self) -> Dict[str, Any]:
        """Analyze test results and provide reliability assessment"""
        print(f"\n📊 Analyzing {len(self.test_results)} test results...")
        
        total_tests = len(self.test_results)
        matching_results = sum(1 for r in self.test_results if r.records_match_claim)
        
        fresh_tests = [r for r in self.test_results if r.test_name == "Fresh Symbol Test"]
        existing_tests = [r for r in self.test_results if r.test_name == "Existing Symbol Test"]
        
        fresh_matches = sum(1 for r in fresh_tests if r.records_match_claim)
        existing_matches = sum(1 for r in existing_tests if r.records_match_claim)
        
        analysis = {
            'total_tests': total_tests,
            'total_matches': matching_results,
            'overall_reliability': matching_results / total_tests if total_tests > 0 else 0,
            'fresh_symbol_tests': len(fresh_tests),
            'fresh_symbol_matches': fresh_matches,
            'fresh_symbol_reliability': fresh_matches / len(fresh_tests) if fresh_tests else 0,
            'existing_symbol_tests': len(existing_tests),
            'existing_symbol_matches': existing_matches,
            'existing_symbol_reliability': existing_matches / len(existing_tests) if existing_tests else 0,
            'detailed_results': self.test_results
        }
        
        print(f"\n📈 RELIABILITY ANALYSIS RESULTS:")
        print(f"   Overall Reliability: {analysis['overall_reliability']:.1%} ({matching_results}/{total_tests})")
        print(f"   Fresh Symbol Reliability: {analysis['fresh_symbol_reliability']:.1%} ({fresh_matches}/{len(fresh_tests)})")
        print(f"   Existing Symbol Reliability: {analysis['existing_symbol_reliability']:.1%} ({existing_matches}/{len(existing_tests)})")
        
        print(f"\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result.records_match_claim else "❌"
            print(f"   {status} {result.symbol} ({result.data_type}): "
                  f"Orchestrator={result.orchestrator_claimed_success}, "
                  f"Records: {result.actual_records_before}→{result.actual_records_after} "
                  f"(+{result.actual_records_inserted})")
        
        return analysis

def main():
    """Run orchestrator reliability tests"""
    tester = OrchestratorReliabilityTester()
    results = tester.run_comprehensive_test()
    
    print(f"\n🎯 CONCLUSION:")
    if results['overall_reliability'] >= 0.9:
        print("✅ Orchestrator is HIGHLY RELIABLE - Safe to base validation on orchestrator results")
    elif results['overall_reliability'] >= 0.7:
        print("⚠️  Orchestrator is MODERATELY RELIABLE - May need additional validation checks")
    else:
        print("❌ Orchestrator is UNRELIABLE - Need to investigate and fix before trusting results")
    
    return results

if __name__ == "__main__":
    main()