#!/usr/bin/env python3
"""
Test Expanded Coverage - See if we can analyze the missing 50 stocks
"""

import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.calculations.composite import CompositeCalculator
from src.data.database import DatabaseManager

def get_unanalyzed_stocks_with_fundamentals(db):
    """Get list of stocks with fundamentals but no composite scores"""
    cursor = db.connection.cursor()
    
    cursor.execute('''
    SELECT DISTINCT fd.symbol
    FROM fundamental_data fd
    JOIN stocks s ON fd.symbol = s.symbol
    LEFT JOIN calculated_metrics cm ON fd.symbol = cm.symbol
    WHERE cm.composite_score IS NULL
    AND fd.net_income IS NOT NULL
    ORDER BY fd.symbol
    ''')
    
    return [row[0] for row in cursor.fetchall()]

def test_expanded_coverage():
    """Test if we can analyze more stocks with enhanced fallback system"""
    print("🧪 Testing Expanded Coverage with Enhanced Fallbacks")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Initialize database
        db = DatabaseManager()
        if not db.connect():
            print("❌ Failed to connect to database")
            return False
        
        # Get unanalyzed stocks
        unanalyzed_stocks = get_unanalyzed_stocks_with_fundamentals(db)
        print(f"📊 Found {len(unanalyzed_stocks)} unanalyzed stocks with fundamental data")
        
        if not unanalyzed_stocks:
            print("✅ All stocks with fundamental data are already analyzed!")
            return True
        
        print(f"🎯 Testing first 10 unanalyzed stocks: {', '.join(unanalyzed_stocks[:10])}")
        
        # Initialize calculator
        calculator = CompositeCalculator()
        
        # Test batch calculation on unanalyzed stocks
        test_symbols = unanalyzed_stocks[:10]  # Test first 10
        
        print("🔄 Attempting to calculate composite scores...")
        batch_results = calculator.calculate_batch_composite(test_symbols, db)
        
        successful_count = len(batch_results)
        failed_count = len(test_symbols) - successful_count
        
        print(f"📈 Results:")
        print(f"   Successful calculations: {successful_count}/{len(test_symbols)}")
        print(f"   Failed calculations: {failed_count}")
        
        if successful_count > 0:
            print(f"\\n✅ SUCCESS: Can analyze {successful_count} additional stocks!")
            print(f"Sample results:")
            for symbol, score_obj in list(batch_results.items())[:5]:
                print(f"   {symbol}: Score={score_obj.composite_score:.1f}")
            
            # Estimate total potential
            success_rate = successful_count / len(test_symbols)
            estimated_total = int(len(unanalyzed_stocks) * success_rate)
            print(f"\\n🎯 POTENTIAL: Could analyze ~{estimated_total} additional stocks")
            print(f"   Current coverage: 476 stocks")
            print(f"   Potential coverage: {476 + estimated_total} stocks")
            print(f"   Coverage increase: +{estimated_total} stocks (+{estimated_total/476*100:.1f}%)")
            
        else:
            print("❌ Could not analyze any additional stocks")
        
        db.close()
        return successful_count > 0
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    success = test_expanded_coverage()
    
    if success:
        print(f"\\n✅ Expanded coverage test successful!")
        print(f"💡 Consider running full analytics update to include more stocks")
    else:
        print(f"\\n❌ Cannot expand coverage with current fallback system")

if __name__ == "__main__":
    main()