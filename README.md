# StockAnalyzer Pro

**Purpose:** Automated stock analysis using a 4-component methodology to identify potentially mispriced stocks
**Status:** Development version with core functionality working, some features in progress
**Current Data:** 503 S&P 500 stocks tracked, 896 with calculated composite scores

## 📊 Methodology Overview

StockAnalyzer Pro uses a weighted 4-component approach:

| Component | Weight | Key Metrics | Status |
|-----------|--------|-------------|--------|
| **🏢 Fundamental** | 40% | P/E, EV/EBITDA, PEG, FCF Yield | ✅ Working |
| **💎 Quality** | 25% | ROE, ROIC, Debt Ratios, Current Ratio | ✅ Working |
| **📈 Growth** | 20% | Revenue Growth, EPS Growth, Stability | ✅ Working |
| **💭 Sentiment** | 15% | News Sentiment + Reddit Collection | ⚠️ Partial |

**Key Features:**
- Sector-aware scoring with 11 industry profiles
- Data quality weighting and validation
- Percentile-based stock categorization
- Interactive dashboard with customizable weights

## 🚦 Current System Status

### ✅ Working Components

**Database & Data Collection:**
- 503 S&P 500 stocks tracked
- 993 fundamental records with financial metrics
- 125,756 price data points for technical analysis
- 17,497 news articles for sentiment analysis
- 1,464 Reddit posts collected

**Calculation Engines:**
- All 4 component calculators functional
- Composite scoring system operational
- Sector adjustments and fallback calculations
- 896 stocks with complete calculated metrics

**User Interface:**
- `analytics_dashboard.py` - Simple, working dashboard with weight customization
- Interactive visualizations and stock rankings
- Methodology guide and metric explanations

**Utilities:**
- Smart data refresh with S&P 500 change detection
- Database backup and restore functionality
- Analytics recalculation tools

### 🚧 In Progress / Needs Fixes

**Reddit Sentiment Calculation:**
- Reddit posts collected but sentiment scores not calculated
- All 1,464 posts currently have sentiment_score = 0.0
- SentimentAnalyzer exists but not integrated with collection

**Advanced Dashboard:**
- `streamlit_app.py` has data management features but integration issues
- Tuple unpacking errors in data versioning
- Two dashboard implementations need consolidation

**Data Management UI:**
- Advanced data refresh interface has connectivity issues
- Quality gating workflow partially implemented

## 🚀 Quick Start

### Prerequisites
```bash
python 3.9+
pip install -r requirements.txt
```

### Launch Working Dashboard
```bash
# Simple dashboard with working features
streamlit run analytics_dashboard.py
```

This provides:
- Stock analysis for 896 S&P 500 companies
- Interactive weight adjustment (40/25/20/15 customizable)
- Professional visualizations and rankings
- Working news sentiment analysis

### Alternative Launch (Advanced Dashboard - Has Issues)
```bash
# Advanced dashboard with data management (needs fixes)
streamlit run streamlit_app.py
```

### Database Setup (If Needed)
```bash
# Initialize empty database
python -c "
from src.data.database import DatabaseManager
db = DatabaseManager()
db.connect()
db.create_tables()
print('Database initialized')
"
```

## 🛠️ Utility Scripts

### Working Utilities
```bash
# Create database backup
python utilities/backup_database.py

# Smart data refresh (checks for stale data)
python utilities/smart_refresh.py --symbols AAPL --data-types fundamentals

# Recalculate all metrics
python utilities/update_analytics.py

# Load complete S&P 500 baseline (if starting fresh)
python scripts/load_sp500_baseline.py
```

### Check System Status
```bash
# Verify database contents
sqlite3 data/stock_data.db "SELECT COUNT(*) FROM stocks; SELECT COUNT(*) FROM calculated_metrics;"

# Check Reddit sentiment status
sqlite3 data/stock_data.db "SELECT COUNT(*) FROM reddit_posts WHERE sentiment_score != 0.0;"
```

## 📋 Current Data Quality

### Excellent Coverage
- **Stocks:** 503/503 S&P 500 companies (100%)
- **Fundamentals:** 993 records with complete financial data
- **Price Data:** 125,756 daily records across all stocks
- **News Sentiment:** 17,497 articles with calculated sentiment scores

### Needs Improvement
- **Reddit Sentiment:** 0/1,464 posts with calculated sentiment (0%)
- **Composite Scores:** 896/503 stocks analyzable (some missing due to data quality)

## 🏗️ System Architecture

```
Data Sources:
├── Yahoo Finance API → Fundamentals, Prices, News
└── Reddit API → Social Discussion Posts

↓

Data Processing:
├── DataCollectionOrchestrator → Fetch & Store
├── SentimentAnalyzer → News Analysis (✅ Working)
├── Calculation Engines → 4-Component Scoring
└── Database → SQLite Storage

↓

User Interface:
├── analytics_dashboard.py → Simple Interface (✅ Working)
└── streamlit_app.py → Advanced Interface (⚠️ Has Issues)
```

## 📁 Project Structure

```
stock-outlier/
├── README.md                   # This file
├── CLAUDE.md                   # Development status & technical details
├── METHODS.md                  # Detailed methodology documentation
├── src/
│   ├── calculations/           # 4-component scoring engines
│   ├── data/                   # Data collection and storage
│   └── analysis/               # Quality analytics
├── utilities/                  # Command-line tools
├── data/stock_data.db         # SQLite database
├── analytics_dashboard.py     # Working dashboard
├── streamlit_app.py           # Advanced dashboard (needs fixes)
└── launch_dashboard.py        # Automated launcher
```

## 🎯 Next Development Priorities

### Priority 1: Reddit Sentiment Fix
- Integrate existing SentimentAnalyzer with refresh_sentiment_only()
- Calculate sentiment scores for all 1,464 collected Reddit posts
- Test sentiment weighting in composite scores

### Priority 2: Dashboard Consolidation
- Fix tuple unpacking errors in streamlit_app.py
- Merge best features from both dashboard implementations
- Provide single, robust user interface

### Priority 3: Data Management
- Complete quality gating workflow implementation
- Fix advanced data refresh interface
- Enhance data versioning system

## 🧪 Testing & Validation

### Verified Working
- Database operations and schema
- All 4 calculation engines
- News sentiment analysis
- Simple dashboard interface
- Backup/restore utilities

### Known Issues
- Reddit sentiment calculation incomplete
- Advanced dashboard has integration errors
- Some data management features non-functional

### Test Commands
```bash
# Test calculation engines
python -c "
from src.calculations.fundamental import FundamentalCalculator
from src.calculations.sentiment import SentimentCalculator
print('Calculation engines available')
"

# Test database
python -c "
from src.data.database import DatabaseManager
db = DatabaseManager()
print('Connected:', db.connect())
"
```

## 🔧 Technology Stack

**Core Technologies:**
- Python 3.9+
- SQLite database
- Streamlit web framework
- Plotly visualizations

**Data Sources:**
- Yahoo Finance (yfinance) - Financial data and news
- Reddit API (praw) - Social sentiment

**Analysis Libraries:**
- TextBlob + VADER - Sentiment analysis
- Pandas - Data manipulation
- NumPy - Mathematical calculations

## ⚠️ Important Notes

**Educational Purpose:** This tool is for educational and research purposes only
**Not Investment Advice:** Always consult qualified financial professionals
**Data Limitations:** Free data sources may have delays or gaps
**Development Status:** Core functionality working, some features in progress

## 🤝 Contributing

**Development Status:** Active development, contributions welcome
**Code Standards:** Follow existing patterns, include tests for new features
**Documentation:** Update METHODS.md for methodology changes

### Development Setup
```bash
git clone <repository-url>
cd stock-outlier
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run analytics_dashboard.py
```

## 📞 Support

**Technical Details:** See CLAUDE.md for current development status
**Methodology:** See METHODS.md for calculation documentation
**Configuration:** Check config/config.yaml for system settings

---

**Disclaimer:** This software is provided as-is for educational purposes. Past performance does not guarantee future results. Always consult qualified financial professionals before making investment decisions.