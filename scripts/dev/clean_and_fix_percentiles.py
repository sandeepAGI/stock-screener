#!/usr/bin/env python3
"""
Clean Duplicates and Fix Percentiles

This script removes duplicate records and calculates percentiles for all stocks.
"""

import sys
import os
import sqlite3
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.calculations.composite import CompositeCalculator, CompositeScore
from src.data.database import DatabaseManager

def clean_duplicate_records(db):
    """Remove duplicate records, keeping only the latest for each symbol"""
    print("🧹 Removing duplicate records...")
    
    cursor = db.connection.cursor()
    
    # Delete older records, keeping only the latest for each symbol
    cursor.execute('''
        DELETE FROM calculated_metrics 
        WHERE id NOT IN (
            SELECT MAX(id) 
            FROM calculated_metrics 
            GROUP BY symbol
        )
    ''')
    
    deleted_count = cursor.rowcount
    db.connection.commit()
    
    print(f"✅ Removed {deleted_count} duplicate records")
    
    # Verify cleanup
    cursor.execute('SELECT COUNT(*) FROM calculated_metrics WHERE composite_score IS NOT NULL')
    remaining_count = cursor.fetchone()[0]
    print(f"📊 Remaining records: {remaining_count}")
    
    return remaining_count

def load_clean_composite_scores(db):
    """Load composite scores after cleanup"""
    print("📊 Loading clean composite scores...")
    
    cursor = db.connection.cursor()
    cursor.execute('''
    SELECT 
        cm.symbol,
        cm.calculation_date,
        cm.fundamental_score,
        cm.quality_score,
        cm.growth_score,
        cm.sentiment_score,
        cm.composite_score,
        cm.methodology_version,
        s.sector
    FROM calculated_metrics cm
    JOIN stocks s ON cm.symbol = s.symbol
    WHERE cm.composite_score IS NOT NULL
    ORDER BY cm.composite_score DESC
    ''')
    
    results = cursor.fetchall()
    
    # Convert to CompositeScore objects
    composite_scores = {}
    for row in results:
        symbol, calc_date, fund_score, qual_score, growth_score, sent_score, comp_score, method_ver, sector = row
        
        # Parse date string
        if isinstance(calc_date, str):
            calc_date = datetime.strptime(calc_date, '%Y-%m-%d').date()
        
        composite_scores[symbol] = CompositeScore(
            symbol=symbol,
            calculation_date=calc_date,
            fundamental_score=fund_score,
            quality_score=qual_score,
            growth_score=growth_score,
            sentiment_score=sent_score,
            fundamental_data_quality=0.8,  # Default values since not stored
            quality_data_quality=0.8,
            growth_data_quality=0.8,
            sentiment_data_quality=0.8,
            composite_score=comp_score,
            overall_data_quality=0.8,
            sector=sector,
            methodology_version=method_ver,
            data_sources_count=4,
            sector_percentile=None,  # Will be calculated
            market_percentile=None,  # Will be calculated
            outlier_category=None    # Will be calculated
        )
    
    print(f"✅ Loaded {len(composite_scores)} clean composite scores")
    return composite_scores

def clean_and_fix_percentiles():
    """Clean duplicates and calculate percentiles"""
    print("🧹 StockAnalyzer Pro - Clean & Fix Percentiles")
    print("=" * 50)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Goal: Clean duplicates and calculate percentiles")
    print()
    
    try:
        # Initialize database
        db = DatabaseManager()
        if not db.connect():
            print("❌ Failed to connect to database")
            return False
        
        # Clean duplicate records
        remaining_count = clean_duplicate_records(db)
        
        if remaining_count == 0:
            print("❌ No records remaining after cleanup")
            return False
        
        # Load clean composite scores
        composite_scores = load_clean_composite_scores(db)
        
        if len(composite_scores) != remaining_count:
            print(f"⚠️  Mismatch: {remaining_count} records vs {len(composite_scores)} loaded")
        
        # Initialize calculator
        calculator = CompositeCalculator()
        
        # Calculate percentiles
        print("🔄 Calculating percentiles and outlier categories...")
        composite_scores_with_percentiles = calculator.calculate_percentiles(composite_scores)
        
        if not composite_scores_with_percentiles:
            print("❌ Failed to calculate percentiles")
            return False
        
        print(f"✅ Calculated percentiles for {len(composite_scores_with_percentiles)} stocks")
        
        # Save updated scores with percentiles
        print("💾 Saving updated scores with percentiles to database...")
        calculator.save_composite_scores(composite_scores_with_percentiles, db)
        
        # Final verification
        print("🔍 Final verification...")
        
        cursor = db.connection.cursor()
        cursor.execute('''
        SELECT 
            COUNT(*) as total,
            COUNT(sector_percentile) as has_sector,
            COUNT(market_percentile) as has_market,
            COUNT(outlier_category) as has_category
        FROM calculated_metrics
        WHERE composite_score IS NOT NULL
        ''')
        
        verification = cursor.fetchone()
        total, has_sector, has_market, has_category = verification
        
        print(f"📊 Final Results:")
        print(f"   Total records: {total}")
        print(f"   With sector percentiles: {has_sector}")
        print(f"   With market percentiles: {has_market}")
        print(f"   With outlier categories: {has_category}")
        
        if has_sector == total and has_market == total and has_category == total:
            print("✅ All percentiles calculated successfully!")
            
            # Show sample results
            cursor.execute('''
            SELECT symbol, composite_score, sector_percentile, market_percentile, outlier_category
            FROM calculated_metrics 
            WHERE composite_score IS NOT NULL AND sector_percentile IS NOT NULL
            ORDER BY composite_score DESC 
            LIMIT 5
            ''')
            
            print(f"\n🎯 Top 5 Undervalued Stocks (Highest Scores):")
            print("   Symbol | Score | Sector %ile | Market %ile | Category")
            print("   " + "-" * 55)
            
            results = cursor.fetchall()
            for row in results:
                symbol, score, sector_pct, market_pct, category = row
                print(f"   {symbol:6} | {score:5.1f} | {sector_pct:10.1f} | {market_pct:10.1f} | {category}")
            
            return True
        else:
            print("❌ Percentile calculation incomplete")
            return False
        
    except Exception as e:
        print(f"❌ Clean and fix failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        if 'db' in locals():
            db.close()

def main():
    """Main function"""
    success = clean_and_fix_percentiles()
    
    if success:
        print(f"\n✅ Clean and fix completed successfully!")
        print(f"🎯 Ready for demo - all percentiles are now calculated")
        print(f"💡 Next steps:")
        print(f"   - Launch dashboard: ./run_demo.sh")
        print(f"   - View analytics: http://localhost:8503")
    else:
        print(f"\n❌ Clean and fix failed!")
        print(f"💡 Check error messages above for debugging")

if __name__ == "__main__":
    main()