#!/usr/bin/env python3
"""
Yahoo Finance Field Test - Verify API Access & Missing Fields
Test Yahoo Finance API connectivity and check specific fields that were 100% missing
"""

import yfinance as yf
from datetime import datetime
import sys

def test_yahoo_finance_fields():
    """Test Yahoo Finance API and check specific missing fields"""
    
    print("🧪 Yahoo Finance API Field Test")
    print("=" * 40)
    print(f"📅 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test with a few representative stocks
    test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'JNJ']
    
    # Fields that were 100% missing in our analysis
    missing_fields = {
        'net_income': 'netIncomeToCommon',
        'total_assets': 'totalAssets', 
        'shareholders_equity': 'shareholderEquity'
    }
    
    # Additional important fields to verify
    verify_fields = {
        'market_cap': 'marketCap',
        'total_revenue': 'totalRevenue',
        'pe_ratio': 'trailingPE',
        'current_price': 'currentPrice',
        'enterprise_value': 'enterpriseValue'
    }
    
    print("🎯 Testing Fields That Were 100% Missing:")
    for field_name, yf_key in missing_fields.items():
        print(f"   • {field_name} → info.get('{yf_key}')")
    print()
    
    results = {}
    
    for symbol in test_symbols:
        print(f"📊 Testing {symbol}...")
        
        try:
            # Create ticker and get info
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info or len(info) < 5:
                print(f"   ❌ No data returned for {symbol}")
                results[symbol] = {'status': 'no_data'}
                continue
            
            # Test the missing fields
            symbol_results = {'status': 'success'}
            
            print(f"   📈 Basic Info:")
            print(f"      Company: {info.get('longName', 'N/A')}")
            print(f"      Sector: {info.get('sector', 'N/A')}")
            print(f"      Market Cap: ${info.get('marketCap', 0):,}" if info.get('marketCap') else "      Market Cap: N/A")
            
            print(f"   🔍 Testing Missing Fields:")
            for field_name, yf_key in missing_fields.items():
                value = info.get(yf_key)
                if value is not None and value != 0:
                    print(f"      ✅ {field_name}: ${value:,}" if isinstance(value, (int, float)) else f"      ✅ {field_name}: {value}")
                    symbol_results[field_name] = value
                else:
                    print(f"      ❌ {field_name}: Not available")
                    symbol_results[field_name] = None
            
            print(f"   ✅ Other Key Fields:")
            for field_name, yf_key in verify_fields.items():
                value = info.get(yf_key)
                if value is not None and value != 0:
                    if isinstance(value, (int, float)) and field_name in ['market_cap', 'total_revenue', 'enterprise_value']:
                        print(f"      ✅ {field_name}: ${value:,}")
                    else:
                        print(f"      ✅ {field_name}: {value}")
                    symbol_results[field_name] = value
                else:
                    print(f"      ⚠️  {field_name}: Not available")
                    symbol_results[field_name] = None
            
            results[symbol] = symbol_results
            print()
            
        except Exception as e:
            print(f"   ❌ Error testing {symbol}: {str(e)}")
            results[symbol] = {'status': 'error', 'error': str(e)}
            print()
    
    # Summary Analysis
    print("📊 SUMMARY ANALYSIS")
    print("-" * 25)
    
    successful_tests = sum(1 for r in results.values() if r.get('status') == 'success')
    print(f"✅ Successfully tested: {successful_tests}/{len(test_symbols)} stocks")
    
    # Analyze field availability
    print(f"\n🎯 Field Availability Analysis:")
    
    for field_name, yf_key in missing_fields.items():
        available_count = sum(1 for r in results.values() 
                            if r.get('status') == 'success' and r.get(field_name) is not None)
        availability_pct = (available_count / successful_tests * 100) if successful_tests > 0 else 0
        
        status = "✅" if availability_pct > 80 else "⚠️" if availability_pct > 50 else "❌"
        print(f"   {status} {field_name} ({yf_key}): {available_count}/{successful_tests} stocks ({availability_pct:.1f}%)")
    
    print(f"\n📋 Field Mapping Verification:")
    print(f"   Our collectors.py uses these mappings in _extract_fundamentals():")
    print(f"   • 'net_income': info.get('netIncomeToCommon')  # ← Check this mapping")
    print(f"   • 'total_assets': info.get('totalAssets')     # ← May not exist in Yahoo Finance")  
    print(f"   • 'shareholders_equity': info.get('shareholderEquity')  # ← Check this mapping")
    
    # API Status Check
    print(f"\n🌐 API Status Assessment:")
    if successful_tests >= 4:
        print(f"   ✅ Yahoo Finance API: HEALTHY - {successful_tests}/{len(test_symbols)} stocks accessible")
        print(f"   🚀 READY for refresh script execution")
    elif successful_tests >= 2:
        print(f"   ⚠️  Yahoo Finance API: PARTIAL - {successful_tests}/{len(test_symbols)} stocks accessible")
        print(f"   🤔 Consider proceeding with caution")
    else:
        print(f"   ❌ Yahoo Finance API: ISSUES - Only {successful_tests}/{len(test_symbols)} stocks accessible")
        print(f"   🛑 NOT recommended to run refresh script now")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    # Check if the missing fields are actually available
    missing_field_found = any(
        any(r.get(field) is not None for r in results.values() if r.get('status') == 'success')
        for field in missing_fields.keys()
    )
    
    if missing_field_found:
        print(f"   ✅ Some missing fields found! Refresh script should help fill gaps")
        print(f"   🔧 Recommended: Run refresh on a few stocks first to test")
        print(f"   📝 Command: python utilities/refresh_data.py --symbols AAPL,MSFT --quiet")
    else:
        print(f"   ⚠️  Missing fields still not available - may be Yahoo Finance API limitations")
        print(f"   🔍 Consider alternative data sources for missing fields")
        print(f"   📊 Refresh script can still update other fields (prices, news, etc.)")
    
    return results

def show_detailed_field_mapping():
    """Show the exact field mappings used in our collectors"""
    print(f"\n🔧 DETAILED FIELD MAPPING (from collectors.py)")
    print("-" * 50)
    
    field_mappings = {
        # Fields that were 100% missing
        'net_income': "info.get('netIncomeToCommon')",
        'total_assets': "info.get('totalAssets')",  # This might not exist!
        'shareholders_equity': "info.get('shareholderEquity')",
        
        # Fields that had some missing values
        'total_debt': "info.get('totalDebt')",
        'free_cash_flow': "info.get('freeCashflow')",
        'operating_cash_flow': "info.get('operatingCashflow')",
        
        # Fields that were complete
        'total_revenue': "info.get('totalRevenue')",
        'market_cap': "info.get('marketCap')",
        'current_price': "info.get('currentPrice')",
        'pe_ratio': "info.get('trailingPE')",
    }
    
    for our_field, yf_mapping in field_mappings.items():
        print(f"   '{our_field}': {yf_mapping}")
    
    print(f"\n📚 To check what fields are actually available:")
    print(f"   ticker = yf.Ticker('AAPL')")
    print(f"   info = ticker.info")
    print(f"   print([key for key in info.keys() if 'asset' in key.lower()])")
    print(f"   print([key for key in info.keys() if 'equity' in key.lower()])")

if __name__ == "__main__":
    print("🚀 Stock Outlier Analytics - Yahoo Finance Field Verification")
    print("=" * 70)
    
    try:
        results = test_yahoo_finance_fields()
        show_detailed_field_mapping()
        
        print(f"\n🎉 Field test completed!")
        print(f"💡 Use this information to decide whether to proceed with refresh script")
        
    except Exception as e:
        print(f"\n❌ Field test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)