# StockAnalyzer Pro - Development Guide
**Last Updated:** December 1, 2025

---

## Documentation Rules

**Before EVERY commit, verify:**
1. `CLAUDE.md` reflects current system state
2. `README.md` has no references to deleted files
3. `docs/CHANGELOG.md` updated for significant changes
4. No obsolete documentation being committed

**File Ownership:**

| File | Purpose | Update When |
|------|---------|-------------|
| `CLAUDE.md` | AI/Dev context | System architecture changes |
| `README.md` | User guide | Features or usage changes |
| `METHODS.md` | Scoring methodology | Algorithm changes |
| `docs/CHANGELOG.md` | Version history | Major milestones |

---

## Current System State

**Branch Structure:**
- `main` - Stable Streamlit dashboard
- `dev` - Development work (Electron migration planned)

**Database:** `data/stock_data.db`
- 503 S&P 500 stocks (511 total, 8 inactive)
- 47,727 news articles with sentiment
- 3,875 Reddit posts with sentiment
- 993 fundamental records
- 125,756 price records

**Working Components:**
- Data collection (Yahoo Finance, Reddit, News APIs)
- Bulk sentiment processing (Anthropic Batch API)
- All 4 calculators (Fundamental, Quality, Growth, Sentiment)
- Composite scoring (40/25/20/15 weighting)
- Dashboard UI (`analytics_dashboard.py`)
- CLI tools (`smart_refresh.py`, `batch_monitor.py`)

---

## Project Structure

```
stock-outlier/
├── analytics_dashboard.py    # Main Streamlit dashboard
├── run_dashboard.sh          # Launch script
├── src/
│   ├── calculations/         # Score calculators
│   ├── data/                 # Data collection & storage
│   └── utils/                # Helper functions
├── utilities/                # CLI tools
├── config/config.yaml        # Configuration
├── data/stock_data.db        # SQLite database
└── docs/
    └── CHANGELOG.md          # Version history
```

---

## Quick Reference Commands

**Run Dashboard:**
```bash
./run_dashboard.sh
# OR
source venv/bin/activate && streamlit run analytics_dashboard.py
```

**Data Collection:**
```bash
python utilities/smart_refresh.py --data-types all --force
python utilities/smart_refresh.py --symbols AAPL MSFT --data-types fundamentals
python utilities/smart_refresh.py --sync-sp500
```

**Sentiment Processing:**
```bash
python utilities/smart_refresh.py --process-sentiment
python utilities/smart_refresh.py --process-sentiment --poll
python utilities/batch_monitor.py
```

**Database:**
```bash
python utilities/backup_database.py
sqlite3 data/stock_data.db "SELECT COUNT(*) FROM stocks WHERE is_active=1"
```

---

## Development Guidelines

1. **User Confirmation First** - Ask before proceeding when in doubt
2. **Test Before Commit** - Verify functionality works
3. **Clean Code** - Remove temporary files, no debug artifacts
4. **Update Docs** - Keep documentation current with code
5. **Descriptive Commits** - Explain what and why

---

## API Keys (.env)

```bash
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
REDDIT_USER_AGENT=StockAnalyzer:v1.0
NEWS_API_KEY=...  # Anthropic API key
```

---

## Current Priority

**Electron Migration** - Replace Streamlit with native desktop app
- FastAPI backend for Python calculations
- React/TypeScript frontend
- Better distribution and user experience

---

## Key Database Tables

| Table | Purpose |
|-------|---------|
| `stocks` | S&P 500 tracking (is_active flag) |
| `fundamental_data` | Financial metrics |
| `price_data` | Historical prices |
| `news_articles` | News with sentiment_score |
| `reddit_posts` | Reddit with sentiment_score |
| `calculated_metrics` | Final composite scores |
| `batch_mapping` | Batch processing tracking |
