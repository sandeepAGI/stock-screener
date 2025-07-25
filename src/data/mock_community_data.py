"""
Mock Yahoo Finance community data for demonstration purposes
"""

from datetime import datetime, timedelta
from typing import List, Dict
import random
from dataclasses import dataclass

@dataclass
class MockCommunityMessage:
    """Mock community message for demonstration"""
    text: str
    author: str
    timestamp: str
    upvotes: int
    downvotes: int
    symbol: str

def generate_mock_community_messages(symbol: str, count: int = 20) -> List[MockCommunityMessage]:
    """
    Generate realistic mock community messages for demonstration
    
    This simulates what would be scraped from Yahoo Finance community boards
    """
    
    # Sample realistic financial community messages
    message_templates = [
        # Bullish sentiment
        f"{symbol} looking strong after earnings beat. Price target $200+",
        f"Great entry point for {symbol} at these levels. Long term hold.",
        f"Love the fundamentals on {symbol}. Revenue growth is impressive.",
        f"{symbol} dividend increase announced. Bullish signal!",
        f"Technical analysis shows {symbol} breaking resistance. Going higher.",
        f"Just added more {symbol} to my portfolio. Undervalued at current prices.",
        f"{symbol} CEO interview was very positive. Exciting times ahead.",
        f"Analysts upgrading {symbol} left and right. Momentum building.",
        f"New product launch from {symbol} looks promising. Innovation continues.",
        f"{symbol} market share expanding in key segments. Bullish outlook.",
        
        # Bearish sentiment  
        f"Concerned about {symbol} guidance for next quarter. Selling pressure likely.",
        f"{symbol} PE ratio seems stretched at these levels. Overvalued?",
        f"Competition heating up for {symbol}. Market share at risk.",
        f"Macro headwinds could hurt {symbol} margins. Cautious here.",
        f"{symbol} insider selling raises red flags. Something brewing?",
        f"Technical breakdown in {symbol} chart. Support levels failing.",
        f"Supply chain issues affecting {symbol} production. Near term headwinds.",
        f"{symbol} regulatory scrutiny increasing. Compliance costs rising.",
        f"Currency headwinds impacting {symbol} international business.",
        f"Debt levels concerning for {symbol}. Balance sheet stress.",
        
        # Neutral/questions
        f"Anyone else watching {symbol} earnings call next week?",
        f"What's your price target for {symbol} this year?",
        f"Thoughts on {symbol} vs competitors? Which is better value?",
        f"How is everyone playing {symbol} options around earnings?",
        f"{symbol} dividend sustainable at current payout ratio?",
        f"Best entry point for {symbol}? Waiting for pullback.",
        f"Long term outlook for {symbol} industry looking good?",
        f"Risk/reward ratio attractive for {symbol} at these prices?",
        f"Tax implications of selling {symbol} position this year?",
        f"Portfolio allocation thoughts? What % {symbol} makes sense?"
    ]
    
    # Sample usernames
    usernames = [
        "BullMarketBill", "ValueInvestor23", "TechAnalyst", "DividendKing", 
        "TraderJoe", "InvestmentGuru", "StockPicker99", "FinanceNerd",
        "MarketWatch", "CashFlowKing", "GrowthSeeker", "ValueHunter",
        "OptionsTrader", "LongTermHold", "DayTrader2025", "RetirementFund",
        "RiskTaker", "ConservativeInv", "MomentumPlay", "ContrarianView"
    ]
    
    messages = []
    base_time = datetime.now()
    
    for i in range(count):
        # Select random message and customize with symbol
        template = random.choice(message_templates)
        message_text = template.replace(f"{symbol}", symbol)
        
        # Generate realistic voting patterns
        # Bullish messages tend to get more upvotes
        if any(word in message_text.lower() for word in ['strong', 'bullish', 'buy', 'long', 'great', 'love', 'positive']):
            upvotes = random.randint(5, 25)
            downvotes = random.randint(0, 5)
        elif any(word in message_text.lower() for word in ['bearish', 'sell', 'concerned', 'overvalued', 'risk', 'cautious']):
            upvotes = random.randint(2, 12)
            downvotes = random.randint(3, 15)
        else:  # Neutral/questions
            upvotes = random.randint(1, 8)
            downvotes = random.randint(0, 3)
        
        # Generate timestamp (within last 24 hours)
        hours_ago = random.randint(1, 24)
        timestamp = (base_time - timedelta(hours=hours_ago)).isoformat()
        
        message = MockCommunityMessage(
            text=message_text,
            author=random.choice(usernames),
            timestamp=timestamp,
            upvotes=upvotes,
            downvotes=downvotes,
            symbol=symbol
        )
        
        messages.append(message)
    
    # Sort by timestamp (newest first)
    messages.sort(key=lambda x: x.timestamp, reverse=True)
    
    return messages

def analyze_mock_community_sentiment(messages: List[MockCommunityMessage]) -> Dict[str, float]:
    """
    Analyze sentiment from mock community messages
    """
    if not messages:
        return {
            'message_count': 0,
            'avg_sentiment': 0.0,
            'bullish_ratio': 0.0,
            'bearish_ratio': 0.0,
            'vote_weighted_sentiment': 0.0,
            'confidence': 0.0
        }
    
    # Analyze message sentiment based on content
    bullish_keywords = ['strong', 'bullish', 'buy', 'long', 'great', 'love', 'positive', 'upgrade', 'beat', 'growth']
    bearish_keywords = ['bearish', 'sell', 'concerned', 'overvalued', 'risk', 'cautious', 'breakdown', 'pressure', 'headwinds']
    
    sentiment_scores = []
    vote_weights = []
    bullish_count = 0
    bearish_count = 0
    
    for msg in messages:
        text_lower = msg.text.lower()
        
        # Calculate sentiment score based on keywords
        bullish_score = sum(1 for word in bullish_keywords if word in text_lower)
        bearish_score = sum(1 for word in bearish_keywords if word in text_lower)
        
        if bullish_score > bearish_score:
            sentiment = 0.3 + (bullish_score * 0.2)  # Positive sentiment
            bullish_count += 1
        elif bearish_score > bullish_score:
            sentiment = -0.3 - (bearish_score * 0.2)  # Negative sentiment  
            bearish_count += 1
        else:
            sentiment = 0.0  # Neutral
        
        # Cap sentiment between -1 and 1
        sentiment = max(-1.0, min(1.0, sentiment))
        sentiment_scores.append(sentiment)
        
        # Calculate vote weight (net upvotes)
        net_votes = msg.upvotes - msg.downvotes
        vote_weight = max(1, net_votes)  # Minimum weight of 1
        vote_weights.append(vote_weight)
    
    # Calculate metrics
    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
    
    # Vote-weighted sentiment
    total_weight = sum(vote_weights)
    vote_weighted_sentiment = sum(score * weight for score, weight in zip(sentiment_scores, vote_weights)) / total_weight
    
    # Ratios
    total_messages = len(messages)
    bullish_ratio = bullish_count / total_messages
    bearish_ratio = bearish_count / total_messages
    
    # Confidence based on message count and vote activity
    confidence = min(1.0, (total_messages / 20) * 0.8 + (sum(vote_weights) / (total_messages * 10)) * 0.2)
    
    return {
        'message_count': total_messages,
        'avg_sentiment': avg_sentiment,
        'bullish_ratio': bullish_ratio,
        'bearish_ratio': bearish_ratio, 
        'vote_weighted_sentiment': vote_weighted_sentiment,
        'confidence': confidence,
        'total_upvotes': sum(msg.upvotes for msg in messages),
        'total_downvotes': sum(msg.downvotes for msg in messages)
    }

# Convenience function for integration
def get_mock_yahoo_community_sentiment(symbol: str, message_count: int = 20) -> Dict[str, float]:
    """
    Generate mock Yahoo Finance community sentiment for demonstration
    
    This simulates what would be extracted from actual Yahoo Finance community scraping
    """
    messages = generate_mock_community_messages(symbol, message_count)
    sentiment_data = analyze_mock_community_sentiment(messages)
    
    # Add metadata
    sentiment_data.update({
        'data_source': 'yahoo_finance_community_mock',
        'collection_time': datetime.now().isoformat(),
        'symbol': symbol
    })
    
    return sentiment_data, messages