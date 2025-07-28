#!/usr/bin/env python3
"""
CSV Export Script - Stock Outlier Analytics
Export all raw data for 503 stocks to CSV file
"""

import sqlite3
import pandas as pd
import os
from datetime import datetime

def export_all_raw_data():
    """Export all raw data to CSV file"""
    
    print("📊 Exporting All Raw Data to CSV")
    print("=" * 40)
    
    try:
        # Connect to database
        conn = sqlite3.connect('data/stock_data.db')
        
        # Create comprehensive query to get all data
        query = """
        SELECT 
            -- Stock information
            s.symbol,
            s.company_name,
            s.sector,
            s.industry,
            s.market_cap as stock_market_cap,
            s.listing_exchange,
            
            -- Latest fundamental data
            fd.reporting_date,
            fd.period_type,
            fd.total_revenue,
            fd.net_income,
            fd.total_assets,
            fd.total_debt,
            fd.shareholders_equity,
            fd.shares_outstanding,
            fd.free_cash_flow,
            fd.operating_cash_flow,
            fd.eps,
            fd.book_value_per_share,
            fd.pe_ratio,
            fd.forward_pe,
            fd.peg_ratio,
            fd.price_to_book,
            fd.enterprise_value,
            fd.ev_to_ebitda,
            fd.return_on_equity,
            fd.return_on_assets,
            fd.debt_to_equity,
            fd.current_ratio,
            fd.quick_ratio,
            fd.revenue_growth,
            fd.earnings_growth,
            fd.revenue_per_share,
            fd.current_price,
            fd.market_cap as fund_market_cap,
            fd.beta,
            fd.dividend_yield,
            fd.week_52_high,
            fd.week_52_low,
            fd.source as fund_source,
            fd.quality_score as fund_quality_score,
            
            -- Latest calculated metrics
            cm.calculation_date,
            cm.fundamental_score,
            cm.quality_score as calc_quality_score,
            cm.growth_score,
            cm.sentiment_score as calc_sentiment_score,
            cm.composite_score,
            cm.sector_percentile,
            cm.data_quality_lower,
            cm.data_quality_upper,
            cm.methodology_version,
            
            -- Price data stats (latest and aggregates)
            pd_latest.date as latest_price_date,
            pd_latest.open as latest_open,
            pd_latest.high as latest_high,
            pd_latest.low as latest_low,
            pd_latest.close as latest_close,
            pd_latest.volume as latest_volume,
            pd_latest.adjusted_close as latest_adj_close,
            
            -- News sentiment aggregates
            news_stats.news_count,
            news_stats.avg_sentiment,
            news_stats.sentiment_std,
            news_stats.positive_news_count,
            news_stats.negative_news_count,
            news_stats.neutral_news_count
            
        FROM stocks s
        
        -- Join with latest fundamental data
        LEFT JOIN (
            SELECT symbol, 
                   reporting_date, period_type, total_revenue, net_income, total_assets, 
                   total_debt, shareholders_equity, shares_outstanding, free_cash_flow, 
                   operating_cash_flow, eps, book_value_per_share, pe_ratio, forward_pe, 
                   peg_ratio, price_to_book, enterprise_value, ev_to_ebitda, 
                   return_on_equity, return_on_assets, debt_to_equity, current_ratio, 
                   quick_ratio, revenue_growth, earnings_growth, revenue_per_share, 
                   current_price, market_cap, beta, dividend_yield, week_52_high, 
                   week_52_low, source, quality_score,
                   ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY reporting_date DESC) as rn
            FROM fundamental_data
        ) fd ON s.symbol = fd.symbol AND fd.rn = 1
        
        -- Join with latest calculated metrics
        LEFT JOIN (
            SELECT symbol, calculation_date, fundamental_score, quality_score, growth_score, 
                   sentiment_score, composite_score, sector_percentile, data_quality_lower, 
                   data_quality_upper, methodology_version,
                   ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY calculation_date DESC) as rn
            FROM calculated_metrics
        ) cm ON s.symbol = cm.symbol AND cm.rn = 1
        
        -- Join with latest price data
        LEFT JOIN (
            SELECT symbol, date, open, high, low, close, volume, adjusted_close,
                   ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY date DESC) as rn
            FROM price_data
        ) pd_latest ON s.symbol = pd_latest.symbol AND pd_latest.rn = 1
        
        -- Join with news sentiment statistics
        LEFT JOIN (
            SELECT symbol,
                   COUNT(*) as news_count,
                   AVG(sentiment_score) as avg_sentiment,
                   CASE 
                       WHEN COUNT(*) > 1 THEN 
                           SQRT(AVG(sentiment_score * sentiment_score) - AVG(sentiment_score) * AVG(sentiment_score))
                       ELSE 0 
                   END as sentiment_std,
                   SUM(CASE WHEN sentiment_score > 0.1 THEN 1 ELSE 0 END) as positive_news_count,
                   SUM(CASE WHEN sentiment_score < -0.1 THEN 1 ELSE 0 END) as negative_news_count,
                   SUM(CASE WHEN sentiment_score >= -0.1 AND sentiment_score <= 0.1 THEN 1 ELSE 0 END) as neutral_news_count
            FROM news_articles
            GROUP BY symbol
        ) news_stats ON s.symbol = news_stats.symbol
        
        WHERE s.is_active = 1
        ORDER BY s.symbol
        """
        
        print("🔄 Executing comprehensive data query...")
        
        # Execute query and create DataFrame
        df = pd.read_sql_query(query, conn)
        
        conn.close()
        
        # Create output filename
        output_filename = "data/CSV-72825-dbsnapshot.csv"
        
        print(f"📝 Writing {len(df)} stock records to CSV...")
        
        # Export to CSV
        df.to_csv(output_filename, index=False)
        
        # Get file size
        file_size_mb = os.path.getsize(output_filename) / (1024 * 1024)
        
        print(f"✅ CSV export completed successfully!")
        print(f"📁 File: {output_filename}")
        print(f"📊 Records: {len(df)} stocks")
        print(f"📏 Columns: {len(df.columns)} data points per stock")
        print(f"💾 File Size: {file_size_mb:.1f} MB")
        
        # Show sample of data
        print(f"\n📋 Sample Data Preview:")
        print(f"{'Symbol':<8} {'Company':<25} {'Sector':<20} {'Composite Score':<15}")
        print("-" * 70)
        
        for i in range(min(5, len(df))):
            row = df.iloc[i]
            company = str(row['company_name'])[:24] if pd.notna(row['company_name']) else "N/A"
            sector = str(row['sector'])[:19] if pd.notna(row['sector']) else "N/A"
            score = f"{row['composite_score']:.1f}" if pd.notna(row['composite_score']) else "N/A"
            print(f"{row['symbol']:<8} {company:<25} {sector:<20} {score:<15}")
        
        # Show column summary
        print(f"\n📊 Data Categories Included:")
        print(f"   🏢 Stock Info: symbol, company_name, sector, industry, market_cap, exchange")
        print(f"   💰 Fundamentals: revenue, income, assets, debt, ratios, growth metrics")
        print(f"   📈 Price Data: latest OHLCV data, 52-week ranges")
        print(f"   🧮 Analytics: composite scores, sector percentiles, quality metrics")
        print(f"   📰 News Sentiment: article counts, sentiment scores, distribution")
        
        # Show data completeness
        total_cells = len(df) * len(df.columns)
        non_null_cells = df.count().sum()
        completeness = (non_null_cells / total_cells) * 100
        
        print(f"\n📈 Data Completeness: {completeness:.1f}% ({non_null_cells:,} of {total_cells:,} cells)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating CSV export: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Stock Outlier Analytics - CSV Data Export")
    print("=" * 50)
    print(f"📅 Export Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = export_all_raw_data()
    
    if success:
        print("\n🎉 Raw data export completed successfully!")
        print("💡 The CSV file contains all available data for analysis and backup purposes")
    else:
        print("\n❌ CSV export failed")
        exit(1)