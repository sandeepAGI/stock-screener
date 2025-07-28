#!/usr/bin/env python3
"""
Add Missing Percentile Columns to Database Schema

This script safely adds the missing market_percentile and outlier_category columns
to the calculated_metrics table.
"""

import sqlite3
import sys
from datetime import datetime

def add_missing_columns():
    """Add missing percentile columns to calculated_metrics table"""
    print("🔧 Adding missing percentile columns to database...")
    
    try:
        conn = sqlite3.connect('data/stock_data.db')
        cursor = conn.cursor()
        
        # Check current schema
        cursor.execute("PRAGMA table_info(calculated_metrics)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"📋 Current columns: {len(column_names)} total")
        
        # Add missing columns
        columns_to_add = [
            ('market_percentile', 'REAL'),
            ('outlier_category', 'TEXT')
        ]
        
        for col_name, col_type in columns_to_add:
            if col_name not in column_names:
                print(f"➕ Adding column: {col_name} ({col_type})")
                cursor.execute(f"ALTER TABLE calculated_metrics ADD COLUMN {col_name} {col_type}")
                conn.commit()
                print(f"✅ Added {col_name}")
            else:
                print(f"✅ Column {col_name} already exists")
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(calculated_metrics)")
        new_columns = cursor.fetchall()
        new_column_names = [col[1] for col in new_columns]
        
        print(f"\n📋 Updated schema: {len(new_column_names)} columns")
        
        required_percentile_columns = ['sector_percentile', 'market_percentile', 'outlier_category']
        all_present = all(col in new_column_names for col in required_percentile_columns)
        
        if all_present:
            print(f"✅ All required percentile columns are now present:")
            for col in required_percentile_columns:
                print(f"   ✅ {col}")
        else:
            missing = [col for col in required_percentile_columns if col not in new_column_names]
            print(f"❌ Still missing columns: {missing}")
            return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error adding columns: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def main():
    """Main function"""
    print("🔧 StockAnalyzer Pro - Database Schema Update")
    print("=" * 50)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Goal: Add missing percentile columns to calculated_metrics table")
    print()
    
    success = add_missing_columns()
    
    if success:
        print(f"\n✅ Database schema update completed successfully!")
        print(f"🔧 Next steps:")
        print(f"1. Update save_composite_scores method to save percentile data")
        print(f"2. Run analytics update to populate percentiles")
        print(f"3. Test dashboard with complete percentile data")
    else:
        print(f"\n❌ Database schema update failed!")
        print(f"💡 You may need to restore from backup if needed")

if __name__ == "__main__":
    main()