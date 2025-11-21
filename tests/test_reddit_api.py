#!/usr/bin/env python3
"""
Test script for Reddit API credentials and functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.helpers import get_reddit_credentials, setup_logging
import praw

def test_reddit_connection():
    """Test Reddit API connection and basic functionality"""
    
    print('🔑 Testing Reddit API Connection')
    print('=' * 50)
    
    # Setup logging
    logger = setup_logging("INFO")
    
    try:
        # Get credentials
        print('📋 Loading Reddit credentials...')
        creds = get_reddit_credentials()
        print(f'✅ Credentials loaded for user: {creds["user_agent"].split("/u/")[1].split(")")[0]}')
        
        # Initialize Reddit instance
        print('🔗 Connecting to Reddit API...')
        reddit = praw.Reddit(
            client_id=creds['client_id'],
            client_secret=creds['client_secret'],
            user_agent=creds['user_agent']
        )
        
        # Test basic connection
        print(f'✅ Connected! Read-only mode: {reddit.read_only}')
        
        # Test subreddit access
        print('\n📊 Testing Financial Subreddit Access:')
        test_subreddits = ['investing', 'stocks', 'SecurityAnalysis']
        
        for subreddit_name in test_subreddits:
            try:
                subreddit = reddit.subreddit(subreddit_name)
                sub_info = f"r/{subreddit.display_name} ({subreddit.subscribers:,} subscribers)"
                print(f'✅ {sub_info}')
            except Exception as e:
                print(f'❌ Failed to access r/{subreddit_name}: {str(e)}')
        
        # Test search functionality for AAPL
        print('\n🔍 Testing Search for AAPL mentions:')
        try:
            subreddit = reddit.subreddit('investing')
            search_results = list(subreddit.search('AAPL', time_filter='week', limit=5))
            
            print(f'✅ Found {len(search_results)} recent AAPL posts in r/investing')
            
            if search_results:
                print('\n📝 Sample Posts:')
                for i, post in enumerate(search_results[:3], 1):
                    print(f'{i}. Title: {post.title[:60]}...')
                    print(f'   Score: {post.score} | Comments: {post.num_comments}')
                    print(f'   Created: {post.created_utc}')
                    print()
                    
        except Exception as e:
            print(f'❌ Search test failed: {str(e)}')
        
        # Test rate limiting info
        print('📊 Rate Limit Status:')
        print(f'   Requests remaining: Check Reddit API headers for current status')
        print(f'   Rate limit: ~100 requests per minute (OAuth authenticated)')
        
        print('\n🎉 Reddit API Test Complete!')
        print('✅ All systems ready for sentiment collection')
        return True
        
    except Exception as e:
        print(f'❌ Reddit API test failed: {str(e)}')
        print('\n🔧 Troubleshooting:')
        print('1. Verify Reddit app credentials in .env file')
        print('2. Ensure app type is set to "script" in Reddit preferences')
        print('3. Check that client_id and client_secret are correct')
        return False

if __name__ == "__main__":
    success = test_reddit_connection()
    if success:
        print('\n🚀 Ready to proceed with Reddit sentiment collection!')
    else:
        print('\n⚠️  Please fix Reddit API setup before proceeding.')
        sys.exit(1)