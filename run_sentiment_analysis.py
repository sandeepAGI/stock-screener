#!/usr/bin/env python3
"""
Run Sentiment Analysis on News Articles
Updates all news articles with proper sentiment scores using TextBlob + VADER analysis
"""

import sys
import os
import sqlite3
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data.sentiment_analyzer import SentimentAnalyzer
import logging

def update_news_sentiment_scores():
    """Update sentiment scores for all news articles in database"""
    
    print("🧠 Running Sentiment Analysis on News Articles")
    print("=" * 50)
    
    try:
        # Initialize sentiment analyzer
        analyzer = SentimentAnalyzer()
        
        # Connect to database
        conn = sqlite3.connect('data/stock_data.db')
        cursor = conn.cursor()
        
        # Get all news articles with zero sentiment scores
        cursor.execute("""
            SELECT id, symbol, title, summary 
            FROM news_articles 
            WHERE sentiment_score = 0 OR sentiment_score IS NULL
        """)
        
        articles = cursor.fetchall()
        total_articles = len(articles)
        
        if total_articles == 0:
            print("✅ All articles already have sentiment scores!")
            return
        
        print(f"📰 Found {total_articles} articles to analyze")
        print("🔄 Processing sentiment analysis...")
        
        updated_count = 0
        
        for i, (article_id, symbol, title, summary) in enumerate(articles):
            if i % 100 == 0:
                print(f"   Progress: {i}/{total_articles} articles processed...")
            
            # Combine title and summary for analysis
            text = f"{title}. {summary or ''}"
            
            # Analyze sentiment
            result = analyzer.analyze_text(text, method='combined')
            
            # Update database with sentiment score
            cursor.execute("""
                UPDATE news_articles 
                SET sentiment_score = ?, data_quality_score = ?
                WHERE id = ?
            """, (result.sentiment_score, result.data_quality, article_id))
            
            updated_count += 1
        
        # Commit all updates
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"\n✅ Successfully updated sentiment scores for {updated_count} articles!")
        
        # Show sample results
        print("\n📊 Sample Results:")
        conn = sqlite3.connect('data/stock_data.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT symbol, title, sentiment_score 
            FROM news_articles 
            WHERE sentiment_score != 0 
            ORDER BY ABS(sentiment_score) DESC 
            LIMIT 5
        """)
        
        sample_results = cursor.fetchall()
        
        print(f"{'Symbol':<8} {'Score':<8} {'Headline'}")
        print("-" * 70)
        
        for symbol, title, score in sample_results:
            print(f"{symbol:<8} {score:<8.3f} {title[:50]}...")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating sentiment scores: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def verify_sentiment_update():
    """Verify that sentiment scores were updated correctly"""
    
    print("\n🔍 Verifying Sentiment Score Updates")
    print("=" * 35)
    
    try:
        conn = sqlite3.connect('data/stock_data.db')
        cursor = conn.cursor()
        
        # Check overall statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN sentiment_score != 0 THEN 1 END) as non_zero,
                AVG(sentiment_score) as avg_score,
                MIN(sentiment_score) as min_score,
                MAX(sentiment_score) as max_score
            FROM news_articles
        """)
        
        total, non_zero, avg_score, min_score, max_score = cursor.fetchone()
        
        print(f"📊 Database Statistics:")
        print(f"   Total Articles: {total}")
        print(f"   Articles with Sentiment: {non_zero}")
        print(f"   Coverage: {(non_zero/total)*100:.1f}%")
        print(f"   Average Sentiment: {avg_score:.3f}")
        print(f"   Range: {min_score:.3f} to {max_score:.3f}")
        
        # Check DECK specifically (mentioned in issue)
        cursor.execute("""
            SELECT title, sentiment_score 
            FROM news_articles 
            WHERE symbol = 'DECK'
            ORDER BY sentiment_score DESC
            LIMIT 5
        """)
        
        deck_results = cursor.fetchall()
        
        print(f"\n🦆 DECK News Headlines (Previously All 0.00):")
        for title, score in deck_results:
            sentiment_emoji = "🟢" if score > 0.1 else "🔴" if score < -0.1 else "⚪"
            print(f"   {sentiment_emoji} {title[:60]}... (Score: {score:.3f})")
        
        cursor.close()
        conn.close()
        
        return non_zero > 0
        
    except Exception as e:
        print(f"❌ Error verifying sentiment updates: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Stock Outlier Analytics - Sentiment Analysis Updater")
    print("=" * 60)
    
    # Run sentiment analysis
    success = update_news_sentiment_scores()
    
    if success:
        # Verify results
        verify_success = verify_sentiment_update()
        
        if verify_success:
            print("\n🎉 Sentiment analysis completed successfully!")
            print("🔄 Restart the dashboard to see updated sentiment scores")
            print("\n💡 Now the headlines should show proper sentiment:")
            print("   🟢 Positive scores for bullish news")
            print("   🔴 Negative scores for bearish news") 
            print("   ⚪ Neutral scores for factual reporting")
        else:
            print("\n⚠️  Sentiment update verification failed")
    else:
        print("\n❌ Sentiment analysis failed")
        sys.exit(1)