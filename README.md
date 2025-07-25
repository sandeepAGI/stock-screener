# StockAnalyzer Pro - POC Implementation

## 🎯 Project Overview

**Goal**: Automated stock mispricing detection using free data sources for S&P 500 stocks  
**Timeline**: 1 week POC with complete 4-component methodology  
**Approach**: Simple, extensible architecture focused on working demonstration

**Repository**: [https://github.com/sandeepAGI/stock-screener](https://github.com/sandeepAGI/stock-screener)  
**License**: MIT License

## 📊 Complete Methodology (All 4 Components)

| Component | Weight | Metrics | Data Source |
|-----------|--------|---------|-------------|
| **Fundamental** | 40% | P/E, EV/EBITDA, PEG, FCF Yield | Yahoo Finance |
| **Quality** | 25% | ROE, ROIC, Debt Ratios | Yahoo Finance |  
| **Growth** | 20% | Revenue Growth, EPS Growth | Yahoo Finance |
| **Sentiment** | 15% | News + Social Sentiment | Yahoo Finance + Reddit |

## 🏗️ Implemented Architecture

```
Data Sources          Database Layer           Calculation Engine       User Interface
┌─────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐   ┌──────────────────┐
│ Yahoo Finance   │───│ SQLite Database     │───│ Fundamental (40%)   │───│ Streamlit        │
│ ✅ Price Data   │   │ ✅ stocks           │   │ • P/E, EV/EBITDA    │   │ • Stock Screener │
│ ✅ Fundamentals │   │ ✅ price_data       │   │ • PEG, FCF Yield    │   │ • Score Breakdown│
│ ✅ News + Sent. │   │ ✅ fundamental_data │   │                     │   │ • Component View │
│                 │   │ ✅ news_articles    │   │ Quality (25%)       │   │ • Export CSV     │
│ Reddit API      │   │ ✅ reddit_posts     │   │ • ROE, ROIC, Debt   │   │                  │
│ ✅ Stock Posts  │───│ ✅ daily_sentiment  │───│                     │───│                  │
│ ✅ Sentiment    │   │ ✅ calculated_metrics│   │ Growth (20%)        │   │                  │
└─────────────────┘   └─────────────────────┘   │ • Revenue Growth    │   │                  │
                                                 │ • EPS Growth        │   │                  │
                                                 │                     │   │                  │
                                                 │ Sentiment (15%)     │   │                  │
                                                 │ ✅ Multi-method     │   │                  │
                                                 │ ✅ TextBlob+VADER   │   │                  │
                                                 │                     │   │                  │
                                                 │ Composite Scorer    │   │                  │
                                                 │ • Weighted Average  │   │                  │
                                                 │ • Stock Ranking     │   │                  │
                                                 └─────────────────────┘   └──────────────────┘
```

## 📁 Current Project Structure

```
stock-screener/
├── README.md                    # Project documentation
├── LICENSE                      # MIT License  
├── technical_requirements.md    # Full technical requirements
├── CLAUDE.md                   # Project instructions for AI
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template (Reddit API)
├── .gitignore                  # Git ignore rules
├── config/
│   └── config.yaml            # ✅ Configuration with S&P 500 sample
├── src/
│   ├── __init__.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── collectors.py       # ✅ Yahoo Finance + Reddit collectors
│   │   ├── database.py         # ✅ Comprehensive SQLite database
│   │   ├── sentiment_analyzer.py # ✅ Multi-method sentiment analysis
│   │   ├── yahoo_community_scraper.py # Yahoo Finance community scraper
│   │   └── mock_community_data.py     # Mock data for demonstration
│   ├── calculations/
│   │   ├── __init__.py         # 🔄 Ready for implementation
│   │   ├── fundamental.py      # ⏳ P/E, EV/EBITDA, PEG, FCF (40%)
│   │   ├── quality.py          # ⏳ ROE, ROIC, Debt ratios (25%)
│   │   ├── growth.py           # ⏳ Revenue/EPS growth (20%)
│   │   ├── sentiment.py        # ⏳ Sentiment scoring (15%)
│   │   └── composite.py        # ⏳ Weighted composite scorer
│   ├── dashboard/
│   │   ├── __init__.py
│   │   └── app.py              # ⏳ Streamlit dashboard
│   └── utils/
│       ├── __init__.py
│       └── helpers.py          # ✅ Config, logging, Reddit setup
├── tests/
│   ├── __init__.py
│   ├── test_collectors.py      # ⏳ Unit tests
│   ├── test_calculations.py
│   └── test_composite.py
└── data/
    └── stock_data.db           # ✅ SQLite database (auto-created)
```

## 🚀 Quick Start

### Prerequisites
```bash
python 3.9+
git clone https://github.com/sandeepAGI/stock-screener.git
cd stock-screener
pip install -r requirements.txt
```

### Setup Reddit API (Required for Sentiment)
1. Create Reddit app at https://www.reddit.com/prefs/apps
2. Copy `.env.example` to `.env` and add your credentials:
```bash
cp .env.example .env
# Edit .env with your Reddit API credentials
```

### Run Database Test (Verify Setup)
```bash
# Test complete data collection and storage
python test_database.py

# Test Reddit API connection
python test_reddit_api.py
```

### Initialize Full Dataset
```bash
# Initialize database and collect sample data
python -c "
from src.data.database import init_database
from src.data.collectors import collect_sp500_sample
db = init_database()
collect_sp500_sample()  # Collect data for 30 S&P 500 stocks
"
```

## 📋 Implementation Status

### ✅ **COMPLETED - Data Foundation**
- **Project Structure**: Complete modular architecture
- **Configuration Management**: YAML config + environment variables
- **Yahoo Finance Integration**: Price, fundamentals, news collection
- **Reddit API Integration**: Multi-subreddit sentiment collection  
- **Comprehensive Database**: SQLite with full audit trail
  - Raw news articles storage for transparency
  - Reddit posts with sentiment scores
  - Daily sentiment aggregation
  - Performance-optimized with indexes
- **Multi-Method Sentiment Analysis**: TextBlob + VADER combined
- **30 Sample S&P 500 Stocks**: Ready for POC testing
- **GitHub Repository**: MIT licensed with proper .gitignore

### 🔄 **IN PROGRESS - Calculation Engines**
- **Fundamental Calculators (40%)**: P/E, EV/EBITDA, PEG, FCF Yield
- Quality Calculators (25%): ROE, ROIC, Debt ratios  
- Growth Calculators (20%): Revenue growth, EPS growth
- Sentiment Scoring (15%): Integration with collected sentiment data

### ⏳ **PENDING - Integration & Dashboard**
- Weighted Composite Scorer (40/25/20/15)
- Streamlit Dashboard with component breakdown
- Unit tests for all calculators
- End-to-end workflow validation

## 🧪 Data Quality Validation

### ✅ Current Test Results
- **Database Integration**: ✅ All tests passing
- **Yahoo Finance Data**: ✅ 251 price records collected (AAPL sample)
- **Fundamental Data**: ✅ P/E, Market Cap, EPS stored successfully  
- **News Collection**: ✅ 10+ articles with sentiment analysis
- **Reddit Integration**: ✅ 5+ posts with sentiment scores
- **Daily Sentiment**: ✅ Combined scoring with confidence metrics

### Sample Data Retrieved (AAPL)
```
📊 Latest Fundamentals:
   P/E Ratio: 33.38
   Market Cap: $3,196,111,814,656
   EPS: $6.41

📰 Recent News: 20 articles with sentiment analysis
   Example: "Apple's Lack Of Clear AI Strategy..." (Sentiment: 0.164)

🔍 Recent Reddit Posts: 5 posts from r/investing, r/stocks  
   Example: "Not all top 10 tech stocks are the same..." (Sentiment: -0.031)

📊 Daily Sentiment: Combined=0.099 (News: 0.104, Reddit: 0.000)
```

## 🔧 Technology Stack

### Core Technologies
- **Python 3.9+**: Main programming language
- **SQLite**: Database with comprehensive schema
- **Streamlit**: Dashboard framework (rapid development)
- **pandas**: Data manipulation and analysis
- **yfinance**: Yahoo Finance API wrapper
- **praw**: Reddit API wrapper

### Implemented Libraries
```txt
streamlit>=1.28.0          # Dashboard framework
pandas>=2.0.0              # Data manipulation  
yfinance>=0.2.18           # Yahoo Finance data
praw>=7.7.0                # Reddit API
plotly>=5.15.0             # Interactive charts
requests>=2.31.0           # HTTP requests
python-dotenv>=1.0.0       # Environment variables
textblob>=0.17.1           # Sentiment analysis
vaderSentiment>=3.3.2      # Financial sentiment analysis
selenium>=4.15.0           # Web scraping (community data)
webdriver-manager>=4.0.0   # Chrome driver management
PyYAML>=6.0.1              # Configuration management
pytest>=7.4.0              # Testing framework
```

## 📊 Database Schema (Implemented)

### Core Tables
- **stocks**: Company metadata (30 S&P 500 sample)
- **price_data**: OHLCV with quality scores
- **fundamental_data**: Complete financial metrics
- **news_articles**: Raw articles with sentiment analysis
- **reddit_posts**: Social sentiment with engagement metrics
- **daily_sentiment**: Aggregated sentiment scores
- **calculated_metrics**: Component scores (ready for calculators)

### Key Features
- **Full Audit Trail**: Raw content stored for transparency
- **Performance Optimized**: Indexed queries for fast retrieval
- **Quality Tracking**: Data source and confidence scoring
- **Extensible Schema**: Ready for additional metrics

## 🎯 Next Steps (Current Phase)

### Immediate Priority: Calculation Engines
1. **Fundamental Calculators** (40% weight)
   - P/E ratio scoring with sector adjustments
   - EV/EBITDA calculation and normalization
   - PEG ratio with growth rate integration
   - Free Cash Flow yield analysis

2. **Quality Metrics** (25% weight)
   - Return on Equity (ROE) calculation
   - Return on Invested Capital (ROIC)
   - Debt-to-Equity ratio analysis
   - Financial strength scoring

3. **Growth Analysis** (20% weight)
   - Revenue growth trend analysis
   - EPS growth consistency
   - Growth quality assessment

4. **Sentiment Integration** (15% weight)
   - News sentiment weighting
   - Social sentiment integration
   - Confidence-based scoring

## 🎯 POC Success Criteria

### ✅ **Data Foundation**: COMPLETE
- Multi-source data collection (Yahoo Finance + Reddit)
- Comprehensive database with audit trail
- Quality sentiment analysis implementation
- 30 stock sample dataset ready

### 🔄 **Calculation Framework**: IN PROGRESS
- All 4 components (40/25/20/15) implemented
- Accurate weighting and normalization
- Component transparency and breakdown

### ⏳ **User Interface**: PENDING
- Interactive Streamlit dashboard
- Stock ranking and filtering
- Component score visualization
- Export capabilities

## 🚀 Getting Involved

### For Developers
1. Fork the repository
2. Set up development environment (see Quick Start)
3. Pick an issue or feature to implement
4. Submit pull request with tests

### For Users/Testers
1. Clone and test the current implementation
2. Report bugs or suggest improvements
3. Validate calculation accuracy
4. Suggest additional metrics or data sources

## 📞 Support & Questions

**Repository**: [https://github.com/sandeepAGI/stock-screener](https://github.com/sandeepAGI/stock-screener)  
**License**: MIT (Open Source)  
**Issues**: Use GitHub Issues for bug reports and feature requests

---

**Last Updated**: July 25, 2025  
**Status**: 🔄 Phase 1 Complete - Implementing Calculation Engines  
**Current Phase**: Fundamental Calculators (40% Component)