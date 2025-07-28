#!/usr/bin/env python3
"""
Simple Refresh Test - Minimal test to update net_income field
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import yfinance as yf
import sqlite3
from datetime import datetime

def simple_refresh_test():
    """Simple test to refresh net_income for a few stocks"""
    
    print("🧪 Simple Refresh Test - Update net_income field")
    print("=" * 50)
    
    # Test symbols
    symbols = ['AAPL', 'MSFT']
    
    # Connect to database
    try:
        conn = sqlite3.connect('data/stock_data.db')
        cursor = conn.cursor()
        print("✅ Connected to database")
        
        for symbol in symbols:
            print(f"\n📊 Processing {symbol}...")
            
            try:
                # Get data from Yahoo Finance
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                if not info:
                    print(f"   ❌ No data from Yahoo Finance")
                    continue
                
                # Extract net_income
                net_income = info.get('netIncomeToCommon')
                
                if net_income is not None:
                    print(f"   ✅ Found net_income: ${net_income:,}")
                    
                    # Update database
                    cursor.execute("""
                        UPDATE fundamental_data 
                        SET net_income = ? 
                        WHERE symbol = ?
                    """, (net_income, symbol))
                    
                    rows_updated = cursor.rowcount
                    print(f"   📝 Updated {rows_updated} records for {symbol}")
                    
                else:
                    print(f"   ⚠️  No net_income data available")
                    
            except Exception as e:
                print(f"   ❌ Error processing {symbol}: {str(e)}")
                continue
        
        # Commit changes
        conn.commit()
        print(f"\n✅ All changes committed to database")
        
        # Verify updates
        print(f"\n🔍 Verifying updates:")
        cursor.execute("""
            SELECT symbol, net_income 
            FROM fundamental_data 
            WHERE symbol IN ('AAPL', 'MSFT') AND net_income IS NOT NULL AND net_income != 0
            ORDER BY symbol
        """)
        
        results = cursor.fetchall()
        for symbol, net_income in results:
            print(f"   ✅ {symbol}: ${net_income:,}")
        
        cursor.close()
        conn.close()
        
        return len(results) > 0
        
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return False

if __name__ == "__main__":
    success = simple_refresh_test()
    
    if success:
        print(f"\n🎉 Simple refresh test completed successfully!")
        print(f"💡 net_income field has been updated from Yahoo Finance")
    else:
        print(f"\n❌ Simple refresh test failed")
        sys.exit(1)