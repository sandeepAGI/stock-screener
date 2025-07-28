#!/usr/bin/env python3
"""
Explore available Yahoo Finance fields for missing data
"""

import yfinance as yf

def explore_available_fields():
    """Explore what fields are actually available in Yahoo Finance"""
    
    print("🔍 Exploring Available Yahoo Finance Fields")
    print("=" * 50)
    
    # Test with AAPL as representative stock
    ticker = yf.Ticker('AAPL')
    info = ticker.info
    
    print(f"📊 Testing with AAPL ({info.get('longName', 'Apple Inc.')})")
    print()
    
    # Look for asset-related fields
    asset_fields = [key for key in info.keys() if 'asset' in key.lower()]
    print(f"🏢 Asset-related fields ({len(asset_fields)} found):")
    for field in sorted(asset_fields):
        value = info.get(field)
        if value is not None:
            if isinstance(value, (int, float)) and abs(value) > 1000:
                print(f"   ✅ {field}: ${value:,}")
            else:
                print(f"   ✅ {field}: {value}")
        else:
            print(f"   ❌ {field}: None")
    print()
    
    # Look for equity-related fields
    equity_fields = [key for key in info.keys() if 'equity' in key.lower()]
    print(f"💰 Equity-related fields ({len(equity_fields)} found):")
    for field in sorted(equity_fields):
        value = info.get(field)
        if value is not None:
            if isinstance(value, (int, float)) and abs(value) > 1000:
                print(f"   ✅ {field}: ${value:,}")
            else:
                print(f"   ✅ {field}: {value}")
        else:
            print(f"   ❌ {field}: None")
    print()
    
    # Look for balance sheet related fields
    balance_fields = [key for key in info.keys() if any(term in key.lower() for term in ['balance', 'book', 'tangible', 'stockholder'])]
    print(f"📊 Balance Sheet related fields ({len(balance_fields)} found):")
    for field in sorted(balance_fields):
        value = info.get(field)
        if value is not None:
            if isinstance(value, (int, float)) and abs(value) > 1000:
                print(f"   ✅ {field}: ${value:,}")
            else:
                print(f"   ✅ {field}: {value}")
        else:
            print(f"   ❌ {field}: None")
    print()
    
    # Show all available fields for reference
    print(f"📝 Total available fields: {len(info.keys())}")
    
    # Check if we can get balance sheet data directly
    print(f"\n🏦 Checking Balance Sheet Data Access:")
    try:
        balance_sheet = ticker.balance_sheet
        if not balance_sheet.empty:
            print(f"   ✅ Balance sheet data available!")
            print(f"   📊 Columns: {len(balance_sheet.columns)} periods")
            print(f"   📈 Rows: {len(balance_sheet.index)} line items")
            
            # Look for our missing fields in balance sheet
            bs_index = balance_sheet.index
            asset_items = [item for item in bs_index if 'asset' in str(item).lower()]
            equity_items = [item for item in bs_index if 'equity' in str(item).lower() or 'stockholder' in str(item).lower()]
            
            print(f"\n   🎯 Relevant Balance Sheet Items:")
            for item in asset_items[:5]:  # Show first 5
                latest_value = balance_sheet.loc[item].iloc[0] if not balance_sheet.loc[item].isna().all() else None
                if latest_value is not None:
                    print(f"      ✅ {item}: ${latest_value:,.0f}")
                else:
                    print(f"      ❌ {item}: No data")
            
            for item in equity_items[:5]:  # Show first 5
                latest_value = balance_sheet.loc[item].iloc[0] if not balance_sheet.loc[item].isna().all() else None
                if latest_value is not None:
                    print(f"      ✅ {item}: ${latest_value:,.0f}")
                else:
                    print(f"      ❌ {item}: No data")
                    
        else:
            print(f"   ❌ No balance sheet data available")
    except Exception as e:
        print(f"   ❌ Error accessing balance sheet: {str(e)}")

if __name__ == "__main__":
    explore_available_fields()