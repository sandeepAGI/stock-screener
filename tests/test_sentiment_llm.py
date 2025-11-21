#!/usr/bin/env python3
"""
Test script for LLM-enhanced sentiment analysis
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.data.sentiment_analyzer import SentimentAnalyzer

def test_sentiment_analysis():
    """Test both traditional and LLM sentiment analysis"""

    # Test texts covering different scenarios
    test_texts = [
        {
            "text": "Apple beats earnings expectations with strong iPhone sales growth 🚀",
            "expected": "positive",
            "type": "earnings_news"
        },
        {
            "text": "AAPL to the moon! Diamond hands baby 💎🙌 This stock is going to explode",
            "expected": "positive",
            "type": "social_media"
        },
        {
            "text": "Company reports disappointing quarterly results, missing analyst estimates",
            "expected": "negative",
            "type": "earnings_news"
        },
        {
            "text": "Tesla stock crashes after Musk's controversial tweets about pricing",
            "expected": "negative",
            "type": "general_financial"
        },
        {
            "text": "The company maintains steady performance with no major changes",
            "expected": "neutral",
            "type": "general_financial"
        }
    ]

    print("Testing LLM-Enhanced Sentiment Analysis")
    print("=" * 50)

    # Test traditional analyzer first
    print("\n1. Testing Traditional Sentiment Analysis:")
    analyzer_traditional = SentimentAnalyzer(use_llm=False)

    for i, test in enumerate(test_texts, 1):
        result = analyzer_traditional.analyze_text(test["text"])
        print(f"\nTest {i} ({test['type']}):")
        print(f"Text: {test['text']}")
        print(f"Expected: {test['expected']}")
        print(f"Score: {result.sentiment_score:.3f} (Method: {result.method})")
        print(f"Quality: {result.data_quality:.3f}")

    # Test LLM analyzer if available
    print("\n\n2. Testing LLM Sentiment Analysis:")
    analyzer_llm = SentimentAnalyzer(use_llm=True)

    if analyzer_llm.claude_client:
        print("✅ Claude LLM client initialized successfully")

        for i, test in enumerate(test_texts, 1):
            try:
                result = analyzer_llm.analyze_text(test["text"])
                print(f"\nTest {i} ({test['type']}):")
                print(f"Text: {test['text']}")
                print(f"Expected: {test['expected']}")
                print(f"Score: {result.sentiment_score:.3f} (Method: {result.method})")
                print(f"Quality: {result.data_quality:.3f}")
                if hasattr(result, 'confidence') and result.confidence:
                    print(f"Confidence: {result.confidence:.3f}")
                if hasattr(result, 'reasoning') and result.reasoning:
                    print(f"Reasoning: {result.reasoning}")

            except Exception as e:
                print(f"❌ Error with test {i}: {str(e)}")

    else:
        print("❌ Claude LLM client not available")
        print("Check your API key in .env file (ANTHROPIC_API_KEY or NEWS_API_KEY)")

        # Check environment variables
        api_key = os.getenv('ANTHROPIC_API_KEY') or os.getenv('NEWS_API_KEY')
        if api_key:
            print(f"✅ API key found: {api_key[:10]}...")
        else:
            print("❌ No API key found in environment")

if __name__ == "__main__":
    test_sentiment_analysis()