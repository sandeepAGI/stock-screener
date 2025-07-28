#!/usr/bin/env python3
"""
Fill Missing net_income Field - Update all stocks with Yahoo Finance data
Based on the successful simple test, expand to all stocks in database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import yfinance as yf
import sqlite3
import time
from datetime import datetime

def fill_missing_net_income():
    """Fill missing net_income field for all stocks in database"""
    
    print("💰 Fill Missing net_income Field - All Stocks")
    print("=" * 55)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Connect to database
        conn = sqlite3.connect('data/stock_data.db')
        cursor = conn.cursor()
        print("✅ Connected to database")
        
        # Get all stocks with missing net_income
        cursor.execute("""
            SELECT DISTINCT fd.symbol 
            FROM fundamental_data fd
            JOIN stocks s ON fd.symbol = s.symbol
            WHERE s.is_active = 1 
            AND (fd.net_income IS NULL OR fd.net_income = 0)
            ORDER BY fd.symbol
        """)
        
        symbols_to_update = [row[0] for row in cursor.fetchall()]
        total_symbols = len(symbols_to_update)
        
        print(f"📊 Found {total_symbols} stocks with missing net_income data")
        
        if total_symbols == 0:
            print("✅ All stocks already have net_income data!")
            return True
        
        print(f"🚀 Starting Yahoo Finance data collection...")
        print()
        
        updated_count = 0
        failed_count = 0
        
        for i, symbol in enumerate(symbols_to_update, 1):
            print(f"📈 Processing {symbol} ({i}/{total_symbols})...", end=" ")
            
            try:
                # Get data from Yahoo Finance
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                if not info or len(info) < 5:
                    print("❌ No data")
                    failed_count += 1
                    continue
                
                # Extract net_income
                net_income = info.get('netIncomeToCommon')
                
                if net_income is not None and net_income != 0:
                    # Update database
                    cursor.execute("""
                        UPDATE fundamental_data 
                        SET net_income = ? 
                        WHERE symbol = ? AND (net_income IS NULL OR net_income = 0)
                    """, (net_income, symbol))
                    
                    rows_updated = cursor.rowcount
                    updated_count += 1
                    print(f"✅ ${net_income:,} ({rows_updated} records)")
                    
                else:
                    print("⚠️  No net_income available")
                    failed_count += 1
                
                # Rate limiting - be respectful to Yahoo Finance
                time.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                failed_count += 1
                continue
        
        # Commit all changes
        conn.commit()
        print(f"\n✅ All changes committed to database")
        
        # Final verification
        print(f"\n📊 FINAL RESULTS:")
        print(f"   ✅ Successfully updated: {updated_count} stocks")
        print(f"   ❌ Failed to update: {failed_count} stocks")
        print(f"   📈 Success rate: {(updated_count / total_symbols * 100):.1f}%")
        
        # Check overall database status
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN net_income IS NOT NULL AND net_income != 0 THEN 1 END) as with_net_income
            FROM fundamental_data
        """)
        
        total_records, records_with_net_income = cursor.fetchone()
        coverage_pct = (records_with_net_income / total_records * 100) if total_records > 0 else 0
        
        print(f"\n📈 Database Coverage Update:")
        print(f"   📊 Total fundamental records: {total_records:,}")
        print(f"   💰 Records with net_income: {records_with_net_income:,}")
        print(f"   📈 Coverage: {coverage_pct:.1f}% (was 0.0% before)")
        
        # Show sample results
        print(f"\n🔍 Sample Updated Records:")
        cursor.execute("""
            SELECT symbol, net_income 
            FROM fundamental_data 
            WHERE net_income IS NOT NULL AND net_income != 0
            ORDER BY ABS(net_income) DESC
            LIMIT 10
        """)
        
        for symbol, net_income in cursor.fetchall():
            print(f"   💰 {symbol}: ${net_income:,}")
        
        cursor.close()
        conn.close()
        
        return updated_count > 0
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Stock Outlier Analytics - Fill Missing net_income Field")
    print("=" * 70)
    
    success = fill_missing_net_income()
    
    if success:
        print(f"\n🎉 net_income field update completed successfully!")
        print(f"💡 This addresses one of the 100% missing fields identified in our analysis")
        print(f"🔄 You can now re-run the missing data analysis to see the improvement")
    else:
        print(f"\n❌ net_income field update failed")
        sys.exit(1)