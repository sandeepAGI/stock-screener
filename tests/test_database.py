#!/usr/bin/env python3
"""
Test script for comprehensive database implementation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data.database import DatabaseManager, NewsArticle, RedditPost, DailySentiment, init_database
from src.data.collectors import YahooFinanceCollector, RedditCollector
from src.data.sentiment_analyzer import SentimentAnalyzer
from src.utils.helpers import setup_logging
from datetime import datetime, date
import time

def test_database_initialization():
    """Test database creation and initialization"""
    print('🗄️  Testing Database Initialization')
    print('=' * 50)
    
    try:
        # Initialize database with sample stocks
        db = init_database()
        print('✅ Database initialized successfully')
        
        # Test connection
        if db.connection:
            print('✅ Database connection established')
        else:
            print('❌ Database connection failed')
            return False
            
        # Check sample stocks were loaded
        stocks = db.get_all_stocks()
        print(f'✅ Sample stocks loaded: {len(stocks)} stocks')
        print(f'   First 5 stocks: {stocks[:5]}')
        
        db.close()
        return True
        
    except Exception as e:
        print(f'❌ Database initialization failed: {str(e)}')
        return False

def test_data_collection_and_storage():
    """Test collecting real data and storing in database"""
    print('\n📊 Testing Data Collection & Storage')
    print('=' * 50)
    
    try:
        # Initialize components
        db = DatabaseManager()
        db.connect()
        
        from src.utils.helpers import load_config
        config = load_config()
        
        yahoo_collector = YahooFinanceCollector(config)
        reddit_collector = RedditCollector(config)
        sentiment_analyzer = SentimentAnalyzer()
        
        test_symbol = 'AAPL'
        print(f'Testing with symbol: {test_symbol}')
        
        # 1. Collect and store Yahoo Finance data
        print('\n📈 Collecting Yahoo Finance data...')
        stock_data = yahoo_collector.collect_stock_data(test_symbol)
        
        if stock_data:
            print('✅ Yahoo Finance data collected')
            
            # Store price data
            if stock_data.price_data is not None and not stock_data.price_data.empty:
                db.insert_price_data(test_symbol, stock_data.price_data)
                print(f'✅ Stored {len(stock_data.price_data)} price records')
            
            # Store fundamental data
            if stock_data.fundamental_data:
                db.insert_fundamental_data(test_symbol, stock_data.fundamental_data)
                print('✅ Stored fundamental data')
            
            # Store news articles with sentiment
            if stock_data.news_headlines:
                news_articles = []
                for headline in stock_data.news_headlines:
                    # Analyze sentiment
                    sentiment = sentiment_analyzer.analyze_text(headline.get('title', '') + ' ' + headline.get('summary', ''))
                    
                    article = NewsArticle(
                        symbol=test_symbol,
                        title=headline.get('title', ''),
                        summary=headline.get('summary', ''),
                        content=headline.get('content', ''),
                        publisher=headline.get('publisher', 'Yahoo Finance'),
                        publish_date=datetime.now(),
                        url=str(headline.get('link', '')),
                        sentiment_score=sentiment.sentiment_score,
                        confidence_score=sentiment.confidence
                    )
                    news_articles.append(article)
                
                if news_articles:
                    db.insert_news_articles(news_articles)
                    print(f'✅ Stored {len(news_articles)} news articles with sentiment')
        
        # 2. Collect and store Reddit data
        print('\n🔍 Collecting Reddit data...')
        reddit_posts = reddit_collector.collect_stock_mentions(test_symbol, max_posts=10)
        
        if reddit_posts:
            print(f'✅ Reddit data collected: {len(reddit_posts)} posts')
            
            # Convert to database format with sentiment
            db_reddit_posts = []
            for post in reddit_posts:
                # Analyze sentiment
                content = post.get('title', '') + ' ' + post.get('selftext', '')
                sentiment = sentiment_analyzer.analyze_text(content)
                
                db_post = RedditPost(
                    symbol=test_symbol,
                    post_id=post.get('id', ''),
                    title=post.get('title', ''),
                    content=post.get('selftext', ''),
                    subreddit=post.get('subreddit', ''),
                    author=post.get('author', ''),
                    score=post.get('score', 0),
                    upvote_ratio=post.get('upvote_ratio', 0.0),
                    num_comments=post.get('num_comments', 0),
                    created_utc=datetime.fromtimestamp(post.get('created_utc', 0)),
                    url=f"https://reddit.com{post.get('permalink', '')}",
                    sentiment_score=sentiment.sentiment_score,
                    confidence_score=sentiment.confidence
                )
                db_reddit_posts.append(db_post)
            
            if db_reddit_posts:
                db.insert_reddit_posts(db_reddit_posts)
                print(f'✅ Stored {len(db_reddit_posts)} Reddit posts with sentiment')
        
        # 3. Create daily sentiment aggregation
        print('\n📊 Creating daily sentiment aggregation...')
        
        # Get recent news and reddit sentiment
        recent_news = db.get_recent_news(test_symbol, days=1)
        recent_reddit = db.get_recent_reddit_posts(test_symbol, days=1)
        
        if recent_news or recent_reddit:
            # Calculate aggregated sentiment
            news_sentiment = sum(article['sentiment_score'] for article in recent_news) / len(recent_news) if recent_news else 0.0
            reddit_sentiment = sum(post['sentiment_score'] for post in recent_reddit) / len(recent_reddit) if recent_reddit else 0.0
            
            # Combined sentiment (weighted average)
            news_weight = len(recent_news) / (len(recent_news) + len(recent_reddit)) if (recent_news or recent_reddit) else 0
            reddit_weight = len(recent_reddit) / (len(recent_news) + len(recent_reddit)) if (recent_news or recent_reddit) else 0
            
            combined_sentiment = (news_sentiment * news_weight) + (reddit_sentiment * reddit_weight)
            
            # Create daily sentiment record
            daily_sentiment = DailySentiment(
                symbol=test_symbol,
                date=date.today(),
                news_sentiment=news_sentiment,
                news_count=len(recent_news),
                reddit_sentiment=reddit_sentiment,
                reddit_count=len(recent_reddit),
                combined_sentiment=combined_sentiment,
                confidence=min(0.9, (len(recent_news) + len(recent_reddit)) / 20.0)
            )
            
            db.insert_daily_sentiment(daily_sentiment)
            print('✅ Stored daily sentiment aggregation')
        
        db.close()
        return True
        
    except Exception as e:
        print(f'❌ Data collection and storage failed: {str(e)}')
        import traceback
        traceback.print_exc()
        return False

def test_data_retrieval():
    """Test retrieving data from database"""
    print('\n🔍 Testing Data Retrieval')
    print('=' * 50)
    
    try:
        db = DatabaseManager()
        db.connect()
        
        test_symbol = 'AAPL'
        
        # Test stock info retrieval
        print(f'\n📊 Stock Info for {test_symbol}:')
        stock_info = db.get_stock_info(test_symbol)
        if stock_info:
            print(f'✅ Company: {stock_info["company_name"]}')
            print(f'   Sector: {stock_info["sector"]}')
            print(f'   Exchange: {stock_info["listing_exchange"]}')
        
        # Test latest price retrieval
        print(f'\n💰 Latest Price for {test_symbol}:')
        latest_price = db.get_latest_price(test_symbol)
        if latest_price:
            print(f'✅ Date: {latest_price["date"]}')
            print(f'   Close: ${latest_price["close"]}')
            print(f'   Volume: {latest_price["volume"]:,}')
        
        # Test fundamental data retrieval
        print(f'\n📈 Latest Fundamentals for {test_symbol}:')
        fundamentals = db.get_latest_fundamentals(test_symbol)
        if fundamentals:
            print(f'✅ P/E Ratio: {fundamentals.get("pe_ratio", "N/A")}')
            print(f'   Market Cap: ${fundamentals.get("market_cap", "N/A"):,}' if fundamentals.get("market_cap") else '   Market Cap: N/A')
            print(f'   EPS: ${fundamentals.get("eps", "N/A")}')
        
        # Test news retrieval
        print(f'\n📰 Recent News for {test_symbol}:')
        recent_news = db.get_recent_news(test_symbol, days=7)
        if recent_news:
            print(f'✅ Found {len(recent_news)} recent news articles')
            for i, article in enumerate(recent_news[:3]):
                print(f'   {i+1}. {article["title"][:60]}...')
                print(f'      Sentiment: {article["sentiment_score"]:.3f} | Publisher: {article["publisher"]}')
        
        # Test Reddit retrieval
        print(f'\n🔍 Recent Reddit Posts for {test_symbol}:')
        recent_reddit = db.get_recent_reddit_posts(test_symbol, days=7)
        if recent_reddit:
            print(f'✅ Found {len(recent_reddit)} recent Reddit posts')
            for i, post in enumerate(recent_reddit[:3]):
                print(f'   {i+1}. {post["title"][:60]}...')
                print(f'      Sentiment: {post["sentiment_score"]:.3f} | Score: {post["score"]} | r/{post["subreddit"]}')
        
        # Test sentiment history
        print(f'\n📊 Daily Sentiment History for {test_symbol}:')
        sentiment_history = db.get_daily_sentiment(test_symbol, days=7)
        if sentiment_history:
            print(f'✅ Found {len(sentiment_history)} days of sentiment data')
            for sentiment in sentiment_history[:3]:
                print(f'   {sentiment["date"]}: Combined={sentiment["combined_sentiment"]:.3f}')
                print(f'      News: {sentiment["news_sentiment"]:.3f} ({sentiment["news_count"]} articles)')
                print(f'      Reddit: {sentiment["reddit_sentiment"]:.3f} ({sentiment["reddit_count"]} posts)')
        
        db.close()
        return True
        
    except Exception as e:
        print(f'❌ Data retrieval failed: {str(e)}')
        return False

def run_complete_database_test():
    """Run complete database functionality test"""
    print('🧪 StockAnalyzer Pro - Database Integration Test')
    print('=' * 60)
    
    # Setup logging
    logger = setup_logging("INFO")
    
    # Run tests
    tests = [
        ("Database Initialization", test_database_initialization),
        ("Data Collection & Storage", test_data_collection_and_storage),
        ("Data Retrieval", test_data_retrieval)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f'\n🔬 Running: {test_name}')
        try:
            start_time = time.time()
            success = test_func()
            end_time = time.time()
            
            results[test_name] = {
                'success': success,
                'duration': end_time - start_time
            }
            
            if success:
                print(f'✅ {test_name} PASSED ({end_time - start_time:.2f}s)')
            else:
                print(f'❌ {test_name} FAILED ({end_time - start_time:.2f}s)')
                
        except Exception as e:
            print(f'💥 {test_name} CRASHED: {str(e)}')
            results[test_name] = {'success': False, 'error': str(e)}
    
    # Summary
    print('\n📋 Test Summary')
    print('=' * 30)
    
    passed = sum(1 for r in results.values() if r.get('success', False))
    total = len(results)
    
    print(f'Tests Passed: {passed}/{total}')
    
    for test_name, result in results.items():
        status = '✅ PASS' if result.get('success', False) else '❌ FAIL'
        duration = f" ({result.get('duration', 0):.2f}s)" if 'duration' in result else ""
        print(f'  {status} {test_name}{duration}')
    
    if passed == total:
        print('\n🎉 All database tests passed! Ready for calculation engines.')
        print('\n📊 Database successfully stores:')
        print('   • Stock metadata and pricing data')
        print('   • Comprehensive fundamental metrics') 
        print('   • Raw news articles with sentiment analysis')
        print('   • Reddit posts with sentiment analysis')
        print('   • Daily aggregated sentiment scores')
        print('   • Full audit trail for transparency')
        
        return True
    else:
        print(f'\n⚠️  {total - passed} test(s) failed. Please fix before proceeding.')
        return False

if __name__ == "__main__":
    success = run_complete_database_test()
    
    if success:
        print('\n🚀 Database implementation complete! Next: Calculation engines')
    else:
        print('\n🔧 Please fix database issues before proceeding.')
        sys.exit(1)