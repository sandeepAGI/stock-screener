#!/usr/bin/env python3
"""
Quick test script for data collectors
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data.collectors import collect_single_stock
from src.utils.helpers import setup_logging

def test_yahoo_collector():
    """Test Yahoo Finance data collection"""
    
    # Setup logging
    logger = setup_logging("INFO")
    
    print("🚀 Testing Yahoo Finance Data Collector")
    print("=" * 50)
    
    # Test with a single stock
    test_symbol = "AAPL"
    print(f"📊 Collecting data for {test_symbol}...")
    
    try:
        stock_data = collect_single_stock(test_symbol)
        
        if stock_data:
            print(f"✅ Successfully collected data for {test_symbol}")
            
            # Display basic info
            print(f"\n📈 Price Data Shape: {stock_data.price_data.shape}")
            print(f"📊 Latest Close Price: ${stock_data.price_data['Close'][-1]:.2f}")
            
            # Display fundamental metrics
            fund = stock_data.fundamental_data
            print(f"\n🏢 Company: {fund.get('company_name', 'N/A')}")
            print(f"🏭 Sector: {fund.get('sector', 'N/A')}")
            print(f"💰 Market Cap: ${fund.get('market_cap', 0):,}")
            print(f"📊 P/E Ratio: {fund.get('pe_ratio', 'N/A')}")
            print(f"💎 ROE: {fund.get('return_on_equity', 'N/A')}")
            
            # Display news count
            print(f"📰 News Headlines: {len(stock_data.news_headlines)}")
            if stock_data.news_headlines:
                print(f"📝 Latest Headline: {stock_data.news_headlines[0]['title'][:80]}...")
                
            print(f"\n✅ Data collection test PASSED for {test_symbol}")
            return True
            
        else:
            print(f"❌ Failed to collect data for {test_symbol}")
            return False
            
    except Exception as e:
        print(f"❌ Error during data collection: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_yahoo_collector()
    
    if success:
        print("\n🎉 Data collector is working correctly!")
        print("Ready to proceed with database setup and calculations.")
    else:
        print("\n⚠️  Data collector needs debugging before proceeding.")
        sys.exit(1)