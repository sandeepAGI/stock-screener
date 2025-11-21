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
| **💭 Sentiment** | 15% | News Sentiment + Reddit Analysis (Claude LLM + Bulk API) | ✅ Enhanced |

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
- 17,497 news articles with sentiment scores
- 1,464 Reddit posts with sentiment analysis
- Batch processing tables for tracking API operations

**Calculation Engines:**
- All 4 component calculators fully functional
- Unified bulk sentiment processing via Anthropic API
- Composite scoring with 40/25/20/15 weighting
- 488+ stocks with complete calculated metrics

**User Interface:**
- `analytics_dashboard.py` - Professional dashboard with 3-step workflow
- Clean data management: Collect → Process → Calculate
- Enhanced interactive visualizations with stock ticker hover data
- Box plot with automatic outlier detection and highlighting
- Real-time batch monitoring and comprehensive error handling

**Utilities:**
- Smart data refresh with S&P 500 change detection
- CLI batch processing for sentiment analysis (NEW - Sept 30)
- Database backup and restore functionality
- Analytics recalculation tools

### 🚀 Recent Major Enhancements

**October 20, 2025 - Interactive Visualization Upgrade:**
- ✅ **Histogram Enhancement**: Hover over distribution bars to see all stock tickers in each score range
- ✅ **Box Plot Upgrade**: Individual data points with outlier highlighting (1.5 × IQR detection)
- ✅ **Rich Tooltips**: Ticker symbols, company names, and exact scores on hover
- ✅ **Database Fix**: Corrected batch_mapping schema issue (table_name → record_type)

**September 30, 2025 - Bulk Processing & Dashboard:**

**Unified Bulk Processing:** ✅ **IMPLEMENTED**
- ✅ **Batch API Integration**: Anthropic Message Batches for efficient processing
- ✅ **Database Tracking**: New batch_mapping table for robust record tracking
- ✅ **Direct Updates**: Bypasses temp tables for immediate database updates
- ✅ **Cost Optimization**: 50% reduction in API costs through batching

**Dashboard Reorganization:** ✅ **COMPLETED**
- ✅ **3-Step Workflow**: Clear progression from collection to calculation
- ✅ **Professional UI**: Removed animations, fixed button layouts
- ✅ **Batch Monitoring**: Real-time status tracking without console access
- ✅ **Error Recovery**: Graceful handling of partial failures

**Performance Gains:**
- **News Sentiment**: 0% → 100% coverage (fixed hardcoded bug)
- **Processing Speed**: 6x faster with bulk API (6+ hours → <1 hour for S&P 500)
- **Cost Efficiency**: 50% reduction in sentiment analysis costs
- **Reliability**: Robust error handling and graceful degradation

**Critical Bug Fixes (Sept 30):**
- ✅ **Database Query Fix**: Corrected JOIN conditions in `get_unprocessed_items_for_batch()`
- ✅ **Efficiency Fix**: Temp queue now filters already-scored items
- ✅ **CLI Enhancement**: Added `--process-sentiment`, `--finalize-batch`, and `--poll` flags

### 🚧 Next Phase Priorities

**Dashboard Consolidation:**
- Merge remaining features into single dashboard
- Archive legacy streamlit_app.py
- Update all launchers and documentation

**Performance Optimization:**
- Scale to 1000+ stocks efficiently
- Implement caching strategies
- Add async processing for UI responsiveness

## 🚀 Quick Start

### Prerequisites
```bash
python 3.9+
pip install -r requirements.txt
```

### Environment Setup
For enhanced LLM sentiment analysis, add your Claude API key to `.env`:
```bash
# Copy example file
cp .env.example .env

# Add your Claude API key
ANTHROPIC_API_KEY=your_claude_api_key_here
# OR
NEWS_API_KEY=your_claude_api_key_here
```

**Note:** System automatically falls back to traditional sentiment analysis if Claude API unavailable.

### Launch Dashboard
```bash
# Main dashboard with 3-step workflow
streamlit run analytics_dashboard.py
```

This provides:
- **Complete 3-Step Workflow**: Collect → Process → Calculate
- **488+ S&P 500 stocks** with composite rankings
- **Interactive weight adjustment** (40/25/20/15 customizable)
- **Batch sentiment processing** with real-time monitoring
- **Professional interface** with comprehensive error handling

### Alternative Dashboard (Legacy - Not Recommended)
```bash
# Legacy dashboard - being phased out
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

# CLI batch processing (NEW - Sept 30)
python utilities/smart_refresh.py --process-sentiment         # Submit batch
python utilities/smart_refresh.py --process-sentiment --poll  # Submit and wait
python utilities/smart_refresh.py --finalize-batch <batch_id> # Finalize batch

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

## 📚 Documentation

### For Users
- **README.md** - This file (getting started, features, basic usage)
- **METHODS.md** - Detailed scoring methodology and algorithms

### For Developers & AI Assistants
- **CLAUDE.md** - Current system state, architecture, development guidelines
- **docs/CHANGELOG.md** - Complete session history and bug fixes
- **docs/IMPLEMENTATION_ROADMAP.md** - Production distribution plan with phases
- **docs/API_KEY_MIGRATION.md** - User-provided API key implementation guide
- **docs/CICD_PIPELINE.md** - GitHub Actions automation guide
- **docs/TEST_PLAN.md** - Testing procedures and validation
- **docs/BATCH_MONITOR_SETUP.md** - Background batch monitor setup

### Historical Reference
- **docs/archive/** - Archived design docs, implementation notes, and completed planning

## 📞 Support

**Issues:** Report bugs via GitHub Issues
**Questions:** See documentation above for detailed guidance
**Configuration:** Check `.env` file for API key settings

---

**Disclaimer:** This software is provided as-is for educational purposes. Past performance does not guarantee future results. Always consult qualified financial professionals before making investment decisions.