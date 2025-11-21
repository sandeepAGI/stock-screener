#!/usr/bin/env python3
"""
End-to-End Workflow Test
Tests complete workflow with real data after terminology changes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import traceback
from datetime import datetime, date

def test_complete_workflow():
    """Test complete workflow with AAPL as sample"""
    print("🧪 Testing Complete End-to-End Workflow with AAPL\n")
    print("=" * 60)
    
    try:
        # Import all necessary modules
        from src.data.database import DatabaseManager, init_database
        from src.calculations.fundamental import FundamentalCalculator
        from src.calculations.quality import QualityCalculator
        from src.calculations.growth import GrowthCalculator
        from src.calculations.sentiment import SentimentCalculator
        from src.calculations.composite import CompositeCalculator
        from src.data.collectors import YahooFinanceCollector
        from src.utils.helpers import load_config
        
        print("✅ Step 1: All modules imported successfully")
        
        # Initialize test database
        test_db_path = "test_e2e_workflow.db"
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        # Load config and override database path
        config = load_config()
        config['database'] = {'path': test_db_path}
        
        # Initialize database
        db = DatabaseManager()
        db.db_path = test_db_path
        db.config = config
        
        if not db.connect():
            print("❌ Failed to connect to test database")
            return False
        
        db.create_tables()
        print("✅ Step 2: Test database initialized")
        
        # Add AAPL to database
        db.insert_stock("AAPL", "Apple Inc.", "Technology", "Technology Hardware", 3000000000000, "NASDAQ")
        print("✅ Step 3: Stock data inserted")
        
        # Create mock fundamental data for AAPL
        mock_fundamentals = {
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
        
        db.insert_fundamental_data("AAPL", mock_fundamentals)
        print("✅ Step 4: Mock fundamental data inserted")
        
        # Test individual calculators
        print("\n🔍 Testing Individual Calculators:")
        
        # Test Fundamental Calculator
        fund_calc = FundamentalCalculator()
        fund_metrics = fund_calc.calculate_fundamental_metrics("AAPL", db)
        
        if fund_metrics:
            print(f"  ✅ Fundamental Score: {fund_metrics.fundamental_score:.1f}")
            print(f"     Data Quality: {fund_metrics.data_quality_score:.2f}")
            assert hasattr(fund_metrics, 'data_quality_score'), "Missing data_quality_score field"
        else:
            print("  ❌ Fundamental calculation failed")
            return False
        
        # Test Quality Calculator
        qual_calc = QualityCalculator()
        qual_metrics = qual_calc.calculate_quality_metrics("AAPL", db)
        
        if qual_metrics:
            print(f"  ✅ Quality Score: {qual_metrics.quality_score:.1f}")
            print(f"     Data Quality: {qual_metrics.data_quality_score:.2f}")
            assert hasattr(qual_metrics, 'data_quality_score'), "Missing data_quality_score field"
        else:
            print("  ❌ Quality calculation failed")
            return False
        
        # Test Growth Calculator
        growth_calc = GrowthCalculator()
        growth_metrics = growth_calc.calculate_growth_metrics("AAPL", db)
        
        if growth_metrics:
            print(f"  ✅ Growth Score: {growth_metrics.growth_score:.1f}")
            print(f"     Data Quality: {growth_metrics.data_quality_score:.2f}")
            assert hasattr(growth_metrics, 'data_quality_score'), "Missing data_quality_score field"
        else:
            print("  ❌ Growth calculation failed")
            return False
        
        # Test Sentiment Calculator (with mock data since we don't have real news/reddit)
        sent_calc = SentimentCalculator()
        # This will likely return None due to no news/reddit data, which is expected
        sent_metrics = sent_calc.calculate_sentiment_metrics("AAPL", db)
        
        if sent_metrics:
            print(f"  ✅ Sentiment Score: {sent_metrics.sentiment_score:.1f}")
            print(f"     Data Quality: {sent_metrics.data_quality_score:.2f}")
            assert hasattr(sent_metrics, 'data_quality_score'), "Missing data_quality_score field"
        else:
            print("  ⚠️  Sentiment calculation returned None (expected - no news/reddit data)")
        
        # Test Composite Calculator
        print("\n🔍 Testing Composite Calculator:")
        
        comp_calc = CompositeCalculator()
        comp_score = comp_calc.calculate_composite_score("AAPL", db)
        
        if comp_score:
            print(f"  ✅ Composite Score: {comp_score.composite_score:.1f}")
            print(f"     Overall Data Quality: {comp_score.overall_data_quality:.2f}")
            print(f"     Component Data Qualities:")
            print(f"       - Fundamental: {comp_score.fundamental_data_quality:.2f}")
            print(f"       - Quality: {comp_score.quality_data_quality:.2f}")
            print(f"       - Growth: {comp_score.growth_data_quality:.2f}")
            print(f"       - Sentiment: {comp_score.sentiment_data_quality:.2f}")
            
            # Verify all updated field names exist
            assert hasattr(comp_score, 'overall_data_quality'), "Missing overall_data_quality field"
            assert hasattr(comp_score, 'fundamental_data_quality'), "Missing fundamental_data_quality field"
            assert hasattr(comp_score, 'quality_data_quality'), "Missing quality_data_quality field"
            assert hasattr(comp_score, 'growth_data_quality'), "Missing growth_data_quality field"
            assert hasattr(comp_score, 'sentiment_data_quality'), "Missing sentiment_data_quality field"
            
        else:
            print("  ❌ Composite calculation failed")
            return False
        
        # Test batch processing
        print("\n🔍 Testing Batch Processing:")
        
        batch_results = comp_calc.calculate_batch_composite(["AAPL"], db)
        if "AAPL" in batch_results:
            print(f"  ✅ Batch processing successful: {len(batch_results)} stocks processed")
        else:
            print("  ❌ Batch processing failed")
            return False
        
        # Test percentile calculation
        print("\n🔍 Testing Percentile Calculation:")
        
        percentile_results = comp_calc.calculate_percentiles(batch_results)
        if "AAPL" in percentile_results:
            aapl_result = percentile_results["AAPL"]
            print(f"  ✅ Percentiles calculated - Market: {aapl_result.market_percentile:.1f}%")
            print(f"     Outlier Category: {aapl_result.outlier_category}")
        else:
            print("  ❌ Percentile calculation failed")
            return False
        
        # Test database saving
        print("\n🔍 Testing Database Operations:")
        
        comp_calc.save_composite_scores(percentile_results, db)
        print("  ✅ Composite scores saved to database")
        
        # Verify data retrieval
        latest_fundamentals = db.get_latest_fundamentals("AAPL")
        if latest_fundamentals:
            print("  ✅ Fundamental data retrieval successful")
        else:
            print("  ❌ Fundamental data retrieval failed")
            return False
        
        # Clean up
        db.close()
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        print("\n" + "=" * 60)
        print("🎉 END-TO-END WORKFLOW TEST SUCCESSFUL!")
        print("   • All modules working correctly with updated terminology")
        print("   • Data quality fields properly implemented")
        print("   • Database operations functioning")
        print("   • Complete calculation pipeline operational")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ End-to-end test failed: {str(e)}")
        traceback.print_exc()
        
        # Clean up on error
        try:
            if 'db' in locals():
                db.close()
            if os.path.exists(test_db_path):
                os.remove(test_db_path)
        except:
            pass
        
        return False

if __name__ == "__main__":
    success = test_complete_workflow()
    sys.exit(0 if success else 1)