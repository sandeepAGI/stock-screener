#!/usr/bin/env python3
"""
Missing Data Analysis - Stock Outlier Analytics
Comprehensive analysis of missing values across all database fields
"""

import sqlite3
import pandas as pd
from datetime import datetime
import numpy as np

def analyze_missing_data():
    """Comprehensive missing data analysis across all tables"""
    
    print("🔍 Deep Dive: Missing Data Analysis")
    print("=" * 50)
    
    try:
        # Connect to database
        conn = sqlite3.connect('data/stock_data.db')
        
        # Get total stock count for reference
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM stocks WHERE is_active = 1")
        total_stocks = cursor.fetchone()[0]
        
        print(f"📊 Analyzing data completeness for {total_stocks} active stocks\n")
        
        # 1. STOCKS table analysis
        print("🏢 STOCKS TABLE ANALYSIS")
        print("-" * 30)
        
        stocks_query = """
        SELECT 
            COUNT(*) as total_records,
            COUNT(symbol) as symbol_count,
            COUNT(company_name) as company_name_count,
            COUNT(sector) as sector_count,
            COUNT(industry) as industry_count,
            COUNT(market_cap) as market_cap_count,
            COUNT(listing_exchange) as listing_exchange_count
        FROM stocks WHERE is_active = 1
        """
        
        stocks_df = pd.read_sql_query(stocks_query, conn)
        stocks_result = stocks_df.iloc[0]
        
        for field in ['symbol', 'company_name', 'sector', 'industry', 'market_cap', 'listing_exchange']:
            count = stocks_result[f'{field}_count']
            missing = total_stocks - count
            missing_pct = (missing / total_stocks) * 100
            status = "✅" if missing == 0 else "⚠️" if missing_pct < 10 else "❌"
            print(f"   {status} {field:<18}: {count:>3}/{total_stocks} ({missing_pct:>5.1f}% missing)")
        
        # 2. FUNDAMENTAL DATA analysis
        print(f"\n💰 FUNDAMENTAL DATA ANALYSIS")
        print("-" * 35)
        
        # Get latest fundamental data for each stock
        fundamental_query = """
        SELECT 
            COUNT(DISTINCT symbol) as stocks_with_data,
            COUNT(total_revenue) as total_revenue_count,
            COUNT(net_income) as net_income_count,
            COUNT(total_assets) as total_assets_count,
            COUNT(total_debt) as total_debt_count,
            COUNT(shareholders_equity) as shareholders_equity_count,
            COUNT(shares_outstanding) as shares_outstanding_count,
            COUNT(free_cash_flow) as free_cash_flow_count,
            COUNT(operating_cash_flow) as operating_cash_flow_count,
            COUNT(eps) as eps_count,
            COUNT(book_value_per_share) as book_value_per_share_count,
            COUNT(pe_ratio) as pe_ratio_count,
            COUNT(forward_pe) as forward_pe_count,
            COUNT(peg_ratio) as peg_ratio_count,
            COUNT(price_to_book) as price_to_book_count,
            COUNT(enterprise_value) as enterprise_value_count,
            COUNT(ev_to_ebitda) as ev_to_ebitda_count,
            COUNT(return_on_equity) as return_on_equity_count,
            COUNT(return_on_assets) as return_on_assets_count,
            COUNT(debt_to_equity) as debt_to_equity_count,
            COUNT(current_ratio) as current_ratio_count,
            COUNT(quick_ratio) as quick_ratio_count,
            COUNT(revenue_growth) as revenue_growth_count,
            COUNT(earnings_growth) as earnings_growth_count,
            COUNT(revenue_per_share) as revenue_per_share_count,
            COUNT(current_price) as current_price_count,
            COUNT(market_cap) as market_cap_count,
            COUNT(beta) as beta_count,
            COUNT(dividend_yield) as dividend_yield_count,
            COUNT(week_52_high) as week_52_high_count,
            COUNT(week_52_low) as week_52_low_count
        FROM (
            SELECT symbol, total_revenue, net_income, total_assets, total_debt, 
                   shareholders_equity, shares_outstanding, free_cash_flow, 
                   operating_cash_flow, eps, book_value_per_share, pe_ratio, 
                   forward_pe, peg_ratio, price_to_book, enterprise_value, 
                   ev_to_ebitda, return_on_equity, return_on_assets, debt_to_equity, 
                   current_ratio, quick_ratio, revenue_growth, earnings_growth, 
                   revenue_per_share, current_price, market_cap, beta, 
                   dividend_yield, week_52_high, week_52_low,
                   ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY reporting_date DESC) as rn
            FROM fundamental_data 
            WHERE symbol IN (SELECT symbol FROM stocks WHERE is_active = 1)
        ) WHERE rn = 1
        """
        
        fundamental_df = pd.read_sql_query(fundamental_query, conn)
        fund_result = fundamental_df.iloc[0]
        
        stocks_with_fundamental = fund_result['stocks_with_data']
        stocks_missing_fundamental = total_stocks - stocks_with_fundamental
        fund_missing_pct = (stocks_missing_fundamental / total_stocks) * 100
        
        print(f"   📈 Stocks with fundamental data: {stocks_with_fundamental}/{total_stocks} ({fund_missing_pct:.1f}% missing)")
        print(f"\n   Key Financial Metrics:")
        
        # Core financials
        core_fields = [
            'total_revenue', 'net_income', 'total_assets', 'total_debt', 
            'shareholders_equity', 'shares_outstanding', 'free_cash_flow', 'operating_cash_flow'
        ]
        
        for field in core_fields:
            count = fund_result[f'{field}_count']
            missing = stocks_with_fundamental - count
            missing_pct = (missing / stocks_with_fundamental) * 100 if stocks_with_fundamental > 0 else 0
            status = "✅" if missing == 0 else "⚠️" if missing_pct < 20 else "❌"
            print(f"      {status} {field:<22}: {count:>3}/{stocks_with_fundamental} ({missing_pct:>5.1f}% missing)")
        
        print(f"\n   Valuation Ratios:")
        ratio_fields = [
            'eps', 'pe_ratio', 'forward_pe', 'peg_ratio', 'price_to_book', 
            'ev_to_ebitda', 'return_on_equity', 'return_on_assets', 'debt_to_equity'
        ]
        
        for field in ratio_fields:
            count = fund_result[f'{field}_count']
            missing = stocks_with_fundamental - count
            missing_pct = (missing / stocks_with_fundamental) * 100 if stocks_with_fundamental > 0 else 0
            status = "✅" if missing == 0 else "⚠️" if missing_pct < 20 else "❌"
            print(f"      {status} {field:<22}: {count:>3}/{stocks_with_fundamental} ({missing_pct:>5.1f}% missing)")
        
        # 3. PRICE DATA analysis
        print(f"\n📈 PRICE DATA ANALYSIS")
        print("-" * 25)
        
        price_query = """
        SELECT 
            COUNT(DISTINCT symbol) as stocks_with_price_data,
            COUNT(*) as total_price_records,
            COUNT(open) as open_count,
            COUNT(high) as high_count,
            COUNT(low) as low_count,
            COUNT(close) as close_count,
            COUNT(volume) as volume_count,
            COUNT(adjusted_close) as adjusted_close_count
        FROM price_data 
        WHERE symbol IN (SELECT symbol FROM stocks WHERE is_active = 1)
        """
        
        price_df = pd.read_sql_query(price_query, conn)
        price_result = price_df.iloc[0]
        
        stocks_with_price = price_result['stocks_with_price_data']
        stocks_missing_price = total_stocks - stocks_with_price
        price_missing_pct = (stocks_missing_price / total_stocks) * 100
        
        print(f"   📊 Stocks with price data: {stocks_with_price}/{total_stocks} ({price_missing_pct:.1f}% missing)")
        print(f"   📅 Total price records: {price_result['total_price_records']:,}")
        
        # Check price data completeness within existing records
        total_price_records = price_result['total_price_records']
        price_fields = ['open', 'high', 'low', 'close', 'volume', 'adjusted_close']
        
        print(f"\n   Price Field Completeness (within {total_price_records:,} records):")
        for field in price_fields:
            count = price_result[f'{field}_count']
            missing = total_price_records - count
            missing_pct = (missing / total_price_records) * 100 if total_price_records > 0 else 0
            status = "✅" if missing == 0 else "⚠️" if missing_pct < 5 else "❌"
            print(f"      {status} {field:<15}: {count:>7,}/{total_price_records:,} ({missing_pct:>5.1f}% missing)")
        
        # 4. NEWS ARTICLES analysis
        print(f"\n📰 NEWS ARTICLES ANALYSIS")
        print("-" * 29)
        
        news_query = """
        SELECT 
            COUNT(DISTINCT symbol) as stocks_with_news,
            COUNT(*) as total_news_articles,
            COUNT(title) as title_count,
            COUNT(summary) as summary_count,
            COUNT(content) as content_count,
            COUNT(publisher) as publisher_count,
            COUNT(publish_date) as publish_date_count,
            COUNT(url) as url_count,
            COUNT(sentiment_score) as sentiment_score_count,
            COUNT(CASE WHEN sentiment_score != 0 THEN 1 END) as non_zero_sentiment_count,
            COUNT(data_quality_score) as data_quality_score_count
        FROM news_articles 
        WHERE symbol IN (SELECT symbol FROM stocks WHERE is_active = 1)
        """
        
        news_df = pd.read_sql_query(news_query, conn)
        news_result = news_df.iloc[0]
        
        stocks_with_news = news_result['stocks_with_news']
        stocks_missing_news = total_stocks - stocks_with_news
        news_missing_pct = (stocks_missing_news / total_stocks) * 100
        
        total_articles = news_result['total_news_articles']
        sentiment_coverage = news_result['non_zero_sentiment_count']
        sentiment_pct = (sentiment_coverage / total_articles) * 100 if total_articles > 0 else 0
        
        print(f"   📺 Stocks with news: {stocks_with_news}/{total_stocks} ({news_missing_pct:.1f}% missing)")
        print(f"   📄 Total articles: {total_articles:,}")
        print(f"   🧠 Articles with sentiment: {sentiment_coverage:,}/{total_articles:,} ({sentiment_pct:.1f}% coverage)")
        
        # Check news field completeness
        news_fields = ['title', 'summary', 'content', 'publisher', 'publish_date', 'url']
        
        print(f"\n   News Field Completeness (within {total_articles:,} articles):")
        for field in news_fields:
            count = news_result[f'{field}_count']
            missing = total_articles - count
            missing_pct = (missing / total_articles) * 100 if total_articles > 0 else 0
            status = "✅" if missing == 0 else "⚠️" if missing_pct < 10 else "❌"
            print(f"      {status} {field:<15}: {count:>7,}/{total_articles:,} ({missing_pct:>5.1f}% missing)")
        
        # 5. CALCULATED METRICS analysis
        print(f"\n🧮 CALCULATED METRICS ANALYSIS")
        print("-" * 34)
        
        metrics_query = """
        SELECT 
            COUNT(DISTINCT symbol) as stocks_with_metrics,
            COUNT(fundamental_score) as fundamental_score_count,
            COUNT(quality_score) as quality_score_count,
            COUNT(growth_score) as growth_score_count,
            COUNT(sentiment_score) as sentiment_score_count,
            COUNT(composite_score) as composite_score_count,
            COUNT(sector_percentile) as sector_percentile_count,
            COUNT(data_quality_lower) as data_quality_lower_count,
            COUNT(data_quality_upper) as data_quality_upper_count
        FROM (
            SELECT symbol, fundamental_score, quality_score, growth_score, 
                   sentiment_score, composite_score, sector_percentile,
                   data_quality_lower, data_quality_upper,
                   ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY calculation_date DESC) as rn
            FROM calculated_metrics 
            WHERE symbol IN (SELECT symbol FROM stocks WHERE is_active = 1)
        ) WHERE rn = 1
        """
        
        metrics_df = pd.read_sql_query(metrics_query, conn)
        metrics_result = metrics_df.iloc[0]
        
        stocks_with_metrics = metrics_result['stocks_with_metrics']
        stocks_missing_metrics = total_stocks - stocks_with_metrics
        metrics_missing_pct = (stocks_missing_metrics / total_stocks) * 100
        
        print(f"   🎯 Stocks with calculated metrics: {stocks_with_metrics}/{total_stocks} ({metrics_missing_pct:.1f}% missing)")
        
        # Check individual metric completeness
        metric_fields = [
            'fundamental_score', 'quality_score', 'growth_score', 'sentiment_score', 
            'composite_score', 'sector_percentile', 'data_quality_lower', 'data_quality_upper'
        ]
        
        print(f"\n   Individual Metric Completeness (within {stocks_with_metrics} analyzed stocks):")
        for field in metric_fields:
            count = metrics_result[f'{field}_count']
            missing = stocks_with_metrics - count
            missing_pct = (missing / stocks_with_metrics) * 100 if stocks_with_metrics > 0 else 0
            status = "✅" if missing == 0 else "⚠️" if missing_pct < 10 else "❌"
            print(f"      {status} {field:<20}: {count:>3}/{stocks_with_metrics} ({missing_pct:>5.1f}% missing)")
        
        # 6. SECTOR-LEVEL ANALYSIS
        print(f"\n🏭 SECTOR-LEVEL MISSING DATA ANALYSIS")
        print("-" * 42)
        
        sector_query = """
        SELECT 
            s.sector,
            COUNT(*) as sector_stocks,
            COUNT(fd.symbol) as with_fundamentals,
            COUNT(pd.symbol) as with_prices,
            COUNT(na.symbol) as with_news,
            COUNT(cm.symbol) as with_metrics
        FROM stocks s
        LEFT JOIN (
            SELECT DISTINCT symbol FROM fundamental_data
        ) fd ON s.symbol = fd.symbol
        LEFT JOIN (
            SELECT DISTINCT symbol FROM price_data
        ) pd ON s.symbol = pd.symbol
        LEFT JOIN (
            SELECT DISTINCT symbol FROM news_articles
        ) na ON s.symbol = na.symbol
        LEFT JOIN (
            SELECT DISTINCT symbol FROM calculated_metrics
        ) cm ON s.symbol = cm.symbol
        WHERE s.is_active = 1
        GROUP BY s.sector
        ORDER BY sector_stocks DESC
        """
        
        sector_df = pd.read_sql_query(sector_query, conn)
        
        print(f"   {'Sector':<25} {'Stocks':<8} {'Fund%':<8} {'Price%':<8} {'News%':<8} {'Metrics%':<8}")
        print("   " + "-" * 65)
        
        for _, row in sector_df.iterrows():
            sector = row['sector'] or 'Unknown'
            stocks = row['sector_stocks']
            fund_pct = (row['with_fundamentals'] / stocks) * 100
            price_pct = (row['with_prices'] / stocks) * 100
            news_pct = (row['with_news'] / stocks) * 100
            metrics_pct = (row['with_metrics'] / stocks) * 100
            
            print(f"   {sector:<25} {stocks:<8} {fund_pct:>5.1f}%  {price_pct:>5.1f}%  {news_pct:>5.1f}%  {metrics_pct:>5.1f}%")
        
        # 7. SUMMARY STATISTICS
        print(f"\n📊 OVERALL DATA COMPLETENESS SUMMARY")
        print("-" * 40)
        
        print(f"   🏢 Basic Stock Info:     {100 - (stocks_missing_fundamental / total_stocks * 100):>5.1f}% complete")
        print(f"   💰 Fundamental Data:     {100 - fund_missing_pct:>5.1f}% complete")
        print(f"   📈 Price History:        {100 - price_missing_pct:>5.1f}% complete")
        print(f"   📰 News & Sentiment:     {100 - news_missing_pct:>5.1f}% complete")
        print(f"   🧮 Analytics Scores:     {100 - metrics_missing_pct:>5.1f}% complete")
        
        # Calculate overall score
        overall_completeness = (
            (100 - fund_missing_pct) * 0.3 +  # Fundamentals weight
            (100 - price_missing_pct) * 0.2 +  # Price weight
            (100 - news_missing_pct) * 0.2 +   # News weight
            (100 - metrics_missing_pct) * 0.3  # Analytics weight
        )
        
        print(f"\n   🎯 OVERALL COMPLETENESS: {overall_completeness:.1f}%")
        
        if overall_completeness >= 90:
            print(f"   ✅ EXCELLENT - Production ready with comprehensive data coverage")
        elif overall_completeness >= 80:
            print(f"   🟢 GOOD - Demo ready with solid data foundation")
        elif overall_completeness >= 70:
            print(f"   ⚠️  FAIR - Usable but with notable data gaps")
        else:
            print(f"   ❌ POOR - Significant data quality issues")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing missing data: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Stock Outlier Analytics - Missing Data Deep Dive")
    print("=" * 60)
    print(f"📅 Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = analyze_missing_data()
    
    if success:
        print(f"\n🎉 Missing data analysis completed!")
        print(f"💡 Use this analysis to prioritize data collection efforts")
    else:
        print(f"\n❌ Analysis failed")
        exit(1)