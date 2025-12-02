# StockAnalyzer Pro

Automated stock analysis using a 4-component methodology to identify potentially mispriced S&P 500 stocks.

## Features

- **Fundamental Analysis (40%)** - P/E, EV/EBITDA, PEG, FCF Yield
- **Quality Metrics (25%)** - ROE, ROIC, Debt Ratios, Current Ratio
- **Growth Analysis (20%)** - Revenue Growth, EPS Growth, Stability
- **Sentiment Analysis (15%)** - News + Reddit sentiment via Claude AI

Additional capabilities:

- Sector-aware scoring with 11 industry profiles
- Percentile-based stock categorization
- Interactive dashboard with customizable weights
- Bulk sentiment processing via Anthropic Batch API

## Requirements

- Python 3.10+
- API Keys: Reddit API, Anthropic API
- macOS/Linux (Windows untested)

## Installation

```bash
# Clone repository
git clone https://github.com/sandeepAGI/stock-screener.git
cd stock-screener

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env with your API keys
```

## Usage

### Run Dashboard

```bash
./run_dashboard.sh
```

Opens at http://localhost:8501

### Data Management (via Dashboard)

1. **Step 1: Collect Data** - Fetch fundamentals, prices, news, Reddit
2. **Step 2: Process Sentiment** - Submit to Claude API for analysis
3. **Step 3: Calculate Scores** - Generate composite rankings

### CLI Tools

```bash
# Refresh all data
python utilities/smart_refresh.py --data-types all --force

# Process sentiment
python utilities/smart_refresh.py --process-sentiment --poll

# Sync S&P 500 changes
python utilities/smart_refresh.py --sync-sp500

# Backup database
python utilities/backup_database.py
```

## Project Structure

```
├── analytics_dashboard.py    # Main dashboard
├── run_dashboard.sh          # Launch script
├── src/
│   ├── calculations/         # Score calculators
│   ├── data/                 # Data collection
│   └── utils/                # Helpers
├── utilities/                # CLI tools
├── config/config.yaml        # Configuration
└── data/stock_data.db        # Database
```

## Methodology

See [METHODS.md](METHODS.md) for detailed scoring algorithms.

## License

MIT License - See [LICENSE](LICENSE)
