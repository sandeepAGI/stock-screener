#!/usr/bin/env python3
"""
Comprehensive Test Suite for Terminology Changes
Tests all components after confidence -> data_quality terminology update
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import traceback
from datetime import datetime, date
from typing import Dict, Any, Optional

def test_imports():
    """Test that all modules can be imported successfully"""
    print("🔍 Testing Module Imports...")
    
    try:
        # Core calculation modules
        from src.calculations.fundamental import FundamentalCalculator, FundamentalMetrics
        from src.calculations.quality import QualityCalculator, QualityMetrics
        from src.calculations.growth import GrowthCalculator, GrowthMetrics
        from src.calculations.sentiment import SentimentCalculator, SentimentMetrics
        from src.calculations.composite import CompositeCalculator, CompositeScore
        
        # Database modules
        from src.data.database import DatabaseManager, NewsArticle, RedditPost, DailySentiment
        from src.data.sentiment_analyzer import SentimentAnalyzer, SentimentScore
        from src.data.collectors import YahooFinanceCollector, SentimentData
        
        # Utility modules
        from src.utils.helpers import load_config
        
        print("✅ All imports successful")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {str(e)}")
        traceback.print_exc()
        return False

def test_dataclass_fields():
    """Test that all dataclass fields have been updated correctly"""
    print("\n🔍 Testing Dataclass Field Updates...")
    
    try:
        from src.calculations.fundamental import FundamentalMetrics
        from src.calculations.quality import QualityMetrics
        from src.calculations.growth import GrowthMetrics
        from src.calculations.sentiment import SentimentMetrics
        from src.calculations.composite import CompositeScore
        from src.data.sentiment_analyzer import SentimentScore
        from src.data.collectors import SentimentData
        from src.data.database import NewsArticle, RedditPost, DailySentiment
        
        # Test fundamental metrics dataclass
        fund_metrics = FundamentalMetrics(
            symbol="TEST",
            calculation_date=date.today(),
            pe_ratio=15.0,
            ev_ebitda=10.0,
            peg_ratio=1.0,
            fcf_yield=0.05,
            pe_score=80.0,
            ev_ebitda_score=85.0,
            peg_score=75.0,
            fcf_yield_score=70.0,
            fundamental_score=77.5,
            data_quality_score=0.8,  # Updated field name
            sector="Technology",
            data_quality=0.8
        )
        assert hasattr(fund_metrics, 'data_quality_score'), "FundamentalMetrics missing data_quality_score"
        
        # Test quality metrics dataclass
        qual_metrics = QualityMetrics(
            symbol="TEST",
            calculation_date=date.today(),
            roe=0.15,
            roic=0.12,
            debt_to_equity=0.3,
            current_ratio=2.0,
            roe_score=80.0,
            roic_score=75.0,
            debt_to_equity_score=85.0,
            current_ratio_score=90.0,
            quality_score=82.5,
            data_quality_score=0.9,  # Updated field name
            sector="Technology",
            data_quality=0.9
        )
        assert hasattr(qual_metrics, 'data_quality_score'), "QualityMetrics missing data_quality_score"
        
        # Test growth metrics dataclass
        growth_metrics = GrowthMetrics(
            symbol="TEST",
            calculation_date=date.today(),
            revenue_growth=0.15,
            eps_growth=0.20,
            revenue_stability=0.8,
            forward_growth=0.18,
            revenue_growth_score=75.0,
            eps_growth_score=80.0,
            revenue_stability_score=85.0,
            forward_growth_score=78.0,
            growth_score=79.0,
            data_quality_score=0.75,  # Updated field name
            sector="Technology",
            data_quality=0.75
        )
        assert hasattr(growth_metrics, 'data_quality_score'), "GrowthMetrics missing data_quality_score"
        
        # Test sentiment metrics dataclass
        sent_metrics = SentimentMetrics(
            symbol="TEST",
            calculation_date=date.today(),
            news_sentiment=0.2,
            social_sentiment=0.1,
            sentiment_momentum=0.05,
            sentiment_volume=25,
            news_sentiment_score=70.0,
            social_sentiment_score=65.0,
            momentum_score=60.0,
            volume_score=75.0,
            sentiment_score=67.5,
            data_quality_score=0.8,  # Updated field name
            sector="Technology",
            data_sources=2,
            news_count=15,
            social_count=10
        )
        assert hasattr(sent_metrics, 'data_quality_score'), "SentimentMetrics missing data_quality_score"
        
        # Test composite score dataclass
        comp_score = CompositeScore(
            symbol="TEST",
            calculation_date=date.today(),
            fundamental_score=77.5,
            quality_score=82.5,
            growth_score=79.0,
            sentiment_score=67.5,
            fundamental_data_quality=0.8,  # Updated field name
            quality_data_quality=0.9,      # Updated field name
            growth_data_quality=0.75,      # Updated field name
            sentiment_data_quality=0.8,    # Updated field name
            composite_score=78.0,
            overall_data_quality=0.81,     # Updated field name
            sector="Technology",
            methodology_version="v1.0",
            data_sources_count=4,
            sector_percentile=None,
            market_percentile=None,
            outlier_category=None
        )
        assert hasattr(comp_score, 'fundamental_data_quality'), "CompositeScore missing fundamental_data_quality"
        assert hasattr(comp_score, 'overall_data_quality'), "CompositeScore missing overall_data_quality"
        
        # Test sentiment analyzer dataclass
        sent_score = SentimentScore(
            text="Test sentiment text",
            sentiment_score=0.3,
            data_quality=0.8,  # Updated field name
            method="combined"
        )
        assert hasattr(sent_score, 'data_quality'), "SentimentScore missing data_quality"
        
        # Test sentiment data dataclass
        sent_data = SentimentData(
            symbol="TEST",
            date=datetime.now(),
            news_sentiment=0.2,
            reddit_sentiment=0.1,
            combined_sentiment=0.15,
            data_quality=0.8,  # Updated field name
            source_count=2
        )
        assert hasattr(sent_data, 'data_quality'), "SentimentData missing data_quality"
        
        # Test database dataclasses
        news_article = NewsArticle(
            symbol="TEST",
            title="Test Article",
            summary="Test summary",
            content="Test content",
            publisher="Test Publisher",
            publish_date=datetime.now(),
            url="http://test.com",
            sentiment_score=0.2,
            data_quality_score=0.8  # Updated field name
        )
        assert hasattr(news_article, 'data_quality_score'), "NewsArticle missing data_quality_score"
        
        reddit_post = RedditPost(
            symbol="TEST",
            post_id="test123",
            title="Test Post",
            content="Test content",
            subreddit="stocks",
            author="testuser",
            score=10,
            upvote_ratio=0.8,
            num_comments=5,
            created_utc=datetime.now(),
            url="http://reddit.com/test",
            sentiment_score=0.1,
            data_quality_score=0.7  # Updated field name
        )
        assert hasattr(reddit_post, 'data_quality_score'), "RedditPost missing data_quality_score"
        
        daily_sentiment = DailySentiment(
            symbol="TEST",
            date=date.today(),
            news_sentiment=0.2,
            news_count=5,
            reddit_sentiment=0.1,
            reddit_count=3,
            combined_sentiment=0.15,
            data_quality=0.75  # Updated field name
        )
        assert hasattr(daily_sentiment, 'data_quality'), "DailySentiment missing data_quality"
        
        print("✅ All dataclass fields updated correctly")
        return True
        
    except Exception as e:
        print(f"❌ Dataclass field test failed: {str(e)}")
        traceback.print_exc()
        return False

def test_database_initialization():
    """Test database initialization with updated schema"""
    print("\n🔍 Testing Database Initialization...")
    
    try:
        from src.data.database import DatabaseManager
        
        # Create test database
        db = DatabaseManager()
        db.db_path = "test_terminology.db"  # Use test database
        
        if db.connect():
            db.create_tables()
            print("✅ Database tables created successfully with updated schema")
            
            # Clean up
            db.close()
            if os.path.exists("test_terminology.db"):
                os.remove("test_terminology.db")
            
            return True
        else:
            print("❌ Failed to connect to test database")
            return False
            
    except Exception as e:
        print(f"❌ Database initialization failed: {str(e)}")
        traceback.print_exc()
        return False

def test_fundamental_calculator():
    """Test fundamental calculator with updated terminology"""
    print("\n🔍 Testing Fundamental Calculator...")
    
    try:
        from src.calculations.fundamental import FundamentalCalculator
        from src.data.database import DatabaseManager
        
        # Create test data
        test_fundamentals = {
            'pe_ratio': 20.0,
            'ev_to_ebitda': 12.0,
            'peg_ratio': 1.2,
            'free_cash_flow': 1000000000,
            'market_cap': 2000000000,
            'earnings_growth': 0.15
        }
        
        calculator = FundamentalCalculator()
        
        # Test individual calculations
        pe_ratio, pe_score = calculator.calculate_pe_ratio(test_fundamentals, "Technology")
        assert pe_ratio == 20.0, "P/E ratio calculation failed"
        assert pe_score > 0, "P/E score should be positive"
        
        fcf_yield, fcf_score = calculator.calculate_fcf_yield(test_fundamentals, "Technology")
        assert fcf_yield == 0.5, "FCF yield calculation failed"  # 1B / 2B = 0.5
        assert fcf_score > 0, "FCF score should be positive"
        
        print("✅ Fundamental calculator working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Fundamental calculator test failed: {str(e)}")
        traceback.print_exc()
        return False

def test_sentiment_analyzer():
    """Test sentiment analyzer with updated terminology"""
    print("\n🔍 Testing Sentiment Analyzer...")
    
    try:
        from src.data.sentiment_analyzer import SentimentAnalyzer, SentimentScore
        
        analyzer = SentimentAnalyzer()
        
        # Test text analysis
        result = analyzer.analyze_text("This stock is performing really well and showing strong growth!")
        
        assert isinstance(result, SentimentScore), "Should return SentimentScore object"
        assert hasattr(result, 'data_quality'), "SentimentScore should have data_quality field"
        assert hasattr(result, 'sentiment_score'), "SentimentScore should have sentiment_score field"
        assert result.sentiment_score > 0, "Should detect positive sentiment"
        assert 0 <= result.data_quality <= 1, "Data quality should be between 0 and 1"
        
        # Test news headlines analysis
        headlines = [
            {'title': 'Company beats earnings expectations', 'summary': 'Strong quarterly results'},
            {'title': 'Stock price surges after positive news', 'summary': 'Market reacts positively'}
        ]
        
        news_result = analyzer.analyze_news_headlines(headlines)
        assert 'data_quality' in news_result, "News analysis should include data_quality"
        assert 'avg_sentiment' in news_result, "News analysis should include avg_sentiment"
        
        print("✅ Sentiment analyzer working correctly with updated terminology")
        return True
        
    except Exception as e:
        print(f"❌ Sentiment analyzer test failed: {str(e)}")
        traceback.print_exc()
        return False

def test_composite_calculator():
    """Test composite calculator with updated terminology"""
    print("\n🔍 Testing Composite Calculator...")
    
    try:
        from src.calculations.composite import CompositeCalculator, CompositeScore
        
        calculator = CompositeCalculator()
        
        # Test data quality threshold checking
        assert 'overall' in calculator.min_data_quality, "Should have overall data quality threshold"
        assert 'fundamental' in calculator.min_data_quality, "Should have fundamental data quality threshold"
        
        # Test sector weight adjustments
        tech_weights = calculator.get_sector_methodology_weights("Technology")
        assert sum(tech_weights.values()) == 1.0, "Sector weights should sum to 1.0"
        
        print("✅ Composite calculator working correctly with updated terminology")
        return True
        
    except Exception as e:
        print(f"❌ Composite calculator test failed: {str(e)}")
        traceback.print_exc()
        return False

def run_comprehensive_test():
    """Run all tests and report results"""
    print("🧪 Starting Comprehensive Terminology Change Testing\n")
    print("=" * 60)
    
    tests = [
        ("Module Imports", test_imports),
        ("Dataclass Fields", test_dataclass_fields),
        ("Database Schema", test_database_initialization),
        ("Fundamental Calculator", test_fundamental_calculator),
        ("Sentiment Analyzer", test_sentiment_analyzer),
        ("Composite Calculator", test_composite_calculator)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} crashed: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Terminology changes successful.")
    else:
        print("⚠️  Some tests failed. Review errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)