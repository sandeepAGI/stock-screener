#!/usr/bin/env python3
"""
Test Percentile Calculations - Safe Testing Before Database Updates

This script tests the percentile calculation logic without modifying the database.
It loads existing composite scores and simulates the percentile calculation process.
"""

import sys
import os
import sqlite3
import pandas as pd
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.calculations.composite import CompositeCalculator
from src.data.database import DatabaseManager

def load_current_composite_scores():
    """Load current composite scores from database"""
    print("📊 Loading current composite scores from database...")
    
    conn = sqlite3.connect('data/stock_data.db')
    
    query = '''
    SELECT 
        cm.symbol,
        cm.composite_score,
        cm.fundamental_score,
        cm.quality_score,
        cm.growth_score,
        cm.sentiment_score,
        s.sector,
        s.company_name
    FROM calculated_metrics cm
    JOIN stocks s ON cm.symbol = s.symbol
    WHERE cm.composite_score IS NOT NULL
    ORDER BY cm.composite_score DESC
    '''
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print(f"✅ Loaded {len(df)} stocks with composite scores")
    return df

def test_percentile_calculations(df):
    """Test percentile calculation logic"""
    print("\n🧪 Testing percentile calculation logic...")
    
    # Calculate market percentiles (should be 0-100 range)
    df['market_percentile'] = df['composite_score'].rank(pct=True) * 100
    
    # Calculate sector percentiles
    df['sector_percentile'] = df.groupby('sector')['composite_score'].rank(pct=True) * 100
    
    # Add outlier categories
    def get_outlier_category(market_pct):
        if market_pct <= 20:
            return 'strong_undervalued'
        elif market_pct <= 35:
            return 'undervalued'
        elif market_pct <= 65:
            return 'fairly_valued'
        elif market_pct <= 80:
            return 'overvalued'
        else:
            return 'strong_overvalued'
    
    df['outlier_category'] = df['market_percentile'].apply(get_outlier_category)
    
    return df

def analyze_results(df):
    """Analyze the calculated percentiles"""
    print("\n📈 Analysis Results:")
    print("=" * 50)
    
    # Market percentile distribution
    print(f"Market Percentiles:")
    print(f"  Min: {df['market_percentile'].min():.1f}")
    print(f"  Max: {df['market_percentile'].max():.1f}")
    print(f"  Mean: {df['market_percentile'].mean():.1f}")
    print(f"  Median: {df['market_percentile'].median():.1f}")
    
    # Sector percentile distribution
    print(f"\nSector Percentiles:")
    print(f"  Min: {df['sector_percentile'].min():.1f}")
    print(f"  Max: {df['sector_percentile'].max():.1f}")
    print(f"  Mean: {df['sector_percentile'].mean():.1f}")
    print(f"  Median: {df['sector_percentile'].median():.1f}")
    
    # Outlier category distribution
    print(f"\nOutlier Categories:")
    category_counts = df['outlier_category'].value_counts().sort_index()
    for category, count in category_counts.items():
        percentage = (count / len(df)) * 100
        print(f"  {category}: {count} stocks ({percentage:.1f}%)")
    
    # Sector analysis
    print(f"\nSector Breakdown:")
    sector_stats = df.groupby('sector').agg({
        'composite_score': ['count', 'mean', 'min', 'max'],
        'sector_percentile': ['min', 'max']
    }).round(1)
    
    for sector in sector_stats.index:
        count = sector_stats.loc[sector, ('composite_score', 'count')]
        mean_score = sector_stats.loc[sector, ('composite_score', 'mean')]
        print(f"  {sector}: {count} stocks, avg score: {mean_score}")

def show_top_examples(df):
    """Show examples of top and bottom stocks"""
    print(f"\n🎯 Top 5 Undervalued (Highest Scores):")
    top_5 = df.nlargest(5, 'composite_score')
    for _, row in top_5.iterrows():
        print(f"  {row['symbol']} ({row['company_name'][:30]}...): "
              f"Score={row['composite_score']:.1f}, "
              f"Market %ile={row['market_percentile']:.1f}, "
              f"Sector %ile={row['sector_percentile']:.1f}, "
              f"Category={row['outlier_category']}")
    
    print(f"\n🎯 Top 5 Overvalued (Lowest Scores):")
    bottom_5 = df.nsmallest(5, 'composite_score')
    for _, row in bottom_5.iterrows():
        print(f"  {row['symbol']} ({row['company_name'][:30]}...): "
              f"Score={row['composite_score']:.1f}, "
              f"Market %ile={row['market_percentile']:.1f}, "
              f"Sector %ile={row['sector_percentile']:.1f}, "
              f"Category={row['outlier_category']}")

def test_database_schema():
    """Test if database has the required columns"""
    print(f"\n🔍 Testing database schema...")
    
    conn = sqlite3.connect('data/stock_data.db')
    cursor = conn.cursor()
    
    # Get column info for calculated_metrics table
    cursor.execute("PRAGMA table_info(calculated_metrics)")
    columns = cursor.fetchall()
    
    column_names = [col[1] for col in columns]
    required_columns = ['sector_percentile', 'market_percentile', 'outlier_category']
    
    print("📋 Current calculated_metrics columns:")
    for col_name in column_names:
        print(f"  ✅ {col_name}")
    
    print(f"\n📋 Required columns for percentiles:")
    for col_name in required_columns:
        if col_name in column_names:
            print(f"  ✅ {col_name} - EXISTS")
        else:
            print(f"  ❌ {col_name} - MISSING")
    
    conn.close()
    
    missing_columns = [col for col in required_columns if col not in column_names]
    return missing_columns

def main():
    """Main testing function"""
    print("🧪 StockAnalyzer Pro - Percentile Calculation Testing")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("⚠️  SAFE MODE: No database modifications will be made")
    print()
    
    try:
        # Test database schema
        missing_columns = test_database_schema()
        
        if missing_columns:
            print(f"\n⚠️  Database schema needs updates for: {', '.join(missing_columns)}")
            print("   This explains why sector percentiles are missing!")
        else:
            print(f"\n✅ Database schema is ready for percentile storage")
        
        # Load current data
        df = load_current_composite_scores()
        
        if df.empty:
            print("❌ No composite scores found in database!")
            return
        
        # Test percentile calculations
        df_with_percentiles = test_percentile_calculations(df)
        
        # Analyze results
        analyze_results(df_with_percentiles)
        
        # Show examples
        show_top_examples(df_with_percentiles)
        
        # Save test results to CSV for review
        output_file = f"test_percentiles_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df_with_percentiles.to_csv(output_file, index=False)
        print(f"\n💾 Test results saved to: {output_file}")
        
        print(f"\n✅ Percentile calculation testing completed successfully!")
        print(f"📊 {len(df_with_percentiles)} stocks processed with calculated percentiles")
        
        if missing_columns:
            print(f"\n🔧 Next Steps:")
            print(f"1. Add missing columns to database schema: {', '.join(missing_columns)}")
            print(f"2. Update save_composite_scores method to include percentile fields")
            print(f"3. Run analytics update to populate percentiles")
        else:
            print(f"\n🔧 Next Steps:")
            print(f"1. Create database backup")
            print(f"2. Update save_composite_scores method")
            print(f"3. Run analytics update to populate percentiles")
        
    except Exception as e:
        print(f"❌ Testing failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()