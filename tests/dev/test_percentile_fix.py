#!/usr/bin/env python3
"""
Test Percentile Fix - Verify composite calculation with percentiles
"""

import sys
import os
import sqlite3
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.calculations.composite import CompositeCalculator
from src.data.database import DatabaseManager

def test_percentile_fix():
    """Test that percentiles are now calculated and saved correctly"""
    print("🧪 Testing percentile fix with small sample...")
    
    # Test with just a few stocks
    test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
    
    try:
        # Initialize calculator and database
        db = DatabaseManager()
        if not db.connect():
            print("❌ Failed to connect to database")
            return False
        
        calculator = CompositeCalculator()
        
        print(f"🔄 Calculating composite scores for {len(test_symbols)} test stocks...")
        
        # Calculate batch composite scores
        composite_scores = calculator.calculate_batch_composite(test_symbols, db)
        
        if not composite_scores:
            print("❌ No composite scores calculated")
            return False
        
        print(f"✅ Calculated {len(composite_scores)} composite scores")
        
        # Calculate percentiles (this adds the percentile fields)
        print("🔄 Calculating percentiles...")
        composite_scores_with_percentiles = calculator.calculate_percentiles(composite_scores)
        
        print(f"✅ Calculated percentiles for {len(composite_scores_with_percentiles)} stocks")
        
        # Save to database (this should now include percentiles)
        print("💾 Saving composite scores with percentiles to database...")
        calculator.save_composite_scores(composite_scores_with_percentiles, db)
        
        # Verify the data was saved correctly
        print("🔍 Verifying percentile data was saved...")
        
        conn = sqlite3.connect('data/stock_data.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT symbol, composite_score, sector_percentile, market_percentile, outlier_category
            FROM calculated_metrics 
            WHERE symbol IN (?, ?, ?, ?, ?)
            AND sector_percentile IS NOT NULL
            ORDER BY composite_score DESC
        ''', test_symbols)
        
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            print("❌ No percentile data found in database")
            return False
        
        print(f"✅ Found {len(results)} stocks with complete percentile data:")
        print("   Symbol | Score | Sector %ile | Market %ile | Category")
        print("   " + "-" * 55)
        
        for row in results:
            symbol, score, sector_pct, market_pct, category = row
            print(f"   {symbol:6} | {score:5.1f} | {sector_pct:10.1f} | {market_pct:10.1f} | {category}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🧪 StockAnalyzer Pro - Percentile Fix Test")
    print("=" * 50)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Goal: Verify percentiles are calculated and saved correctly")
    print()
    
    success = test_percentile_fix()
    
    if success:
        print(f"\n✅ Percentile fix test passed!")
        print(f"🎯 Ready to run full analytics update for all 476 stocks")
    else:
        print(f"\n❌ Percentile fix test failed!")
        print(f"💡 Check error messages above for debugging")

if __name__ == "__main__":
    main()