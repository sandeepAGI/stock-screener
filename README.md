# StockAnalyzer Pro

**AI-Powered Stock Analysis for the S&P 500**

[![Platform](https://img.shields.io/badge/Platform-macOS-blue.svg)](https://www.apple.com/macos/)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)]()

---

## 📊 What is StockAnalyzer Pro?

StockAnalyzer Pro is a comprehensive stock analysis tool that uses AI-powered sentiment analysis and multi-factor scoring to identify potentially undervalued and overvalued stocks in the S&P 500.

### Key Features:
- 🤖 **AI-Powered Sentiment Analysis** using Claude (Anthropic)
- 📊 **Multi-Factor Scoring** (Fundamental, Quality, Growth, Sentiment)
- 📱 **Social Media Tracking** via Reddit
- 🔐 **Secure Credentials** stored in macOS Keychain
- 📈 **Interactive Dashboard** with real-time rankings
- 🚀 **Automated CI/CD** for seamless releases

---

## 🎯 For End Users

### Download & Install

**Latest Release:** [Download StockAnalyzer Pro](https://github.com/yourusername/stock-outlier/releases/latest)

#### Quick Install:
1. Download `StockAnalyzer-macOS-v*.*.*.dmg`
2. Open the DMG file
3. Drag `StockAnalyzer.app` to Applications
4. Right-click → Open (for first launch)
5. Follow the setup wizard

**Full Instructions:** See [User Installation Guide](docs/USER_INSTALLATION_GUIDE.md)

### Requirements:
- **macOS:** 10.13 (High Sierra) or later
- **Reddit API:** Free ([Get credentials](https://www.reddit.com/prefs/apps))
- **Claude API:** Paid ([Get API key](https://console.anthropic.com/))

**Cost:** Reddit is free, Claude is usage-based (~$1-5 for small portfolios)

---

## 👨‍💻 For Developers

### Quick Start

```bash
# Clone repository
git clone https://github.com/yourusername/stock-outlier.git
cd stock-outlier

# Install dependencies
pip install -r requirements.txt

# Set up API keys (for development)
cp .env.example .env
# Edit .env with your API keys

# Run dashboard
streamlit run analytics_dashboard.py
```

### Development Workflow

```bash
# Work on main branch
git checkout main

# Make changes
git add .
git commit -m "feat: your feature"
git push

# Tests run automatically via GitHub Actions
```

**See:** [Getting Started Guide](docs/GETTING_STARTED.md) for detailed instructions

---

## 📦 Building & Distribution

### Build macOS Application

```bash
# 1. Ensure all tests pass
python -m pytest tests/ -v

# 2. Build with PyInstaller
pyinstaller StockAnalyzer.spec

# 3. Test the build
open dist/StockAnalyzer.app

# 4. Create DMG for distribution
hdiutil create -volname "StockAnalyzer Pro" \
  -srcfolder dist/StockAnalyzer.app \
  -ov -format UDZO \
  StockAnalyzer-macOS-v1.0.0.dmg
```

**Estimated build time:** 5-10 minutes

**See:** [Build and Distribute Guide](docs/BUILD_AND_DISTRIBUTE.md)

---

## 🚀 Automated CI/CD Pipeline

### Promote to Production

**Via GitHub UI:**
1. Go to **Actions** → **Promote Main to Prod**
2. Click **Run workflow**
3. Enter version: `v1.0.0`
4. Check **Create Release**
5. Click **Run workflow**

**Via Command Line:**
```bash
gh workflow run promote-to-prod.yml -f version=v1.0.0
```

**What Happens:**
- ✅ Tests run automatically
- ✅ Code merges main → prod
- ✅ macOS app builds automatically
- ✅ DMG created
- ✅ GitHub Release published

**Total time:** ~15 minutes from promotion to release!

**See:** [CI/CD Usage Guide](docs/CICD_USAGE.md) | [Quick Reference](docs/CICD_QUICK_REFERENCE.md)

---

## 📋 Methodology

StockAnalyzer Pro uses a weighted 4-component approach:

| Component | Weight | Key Metrics |
|-----------|--------|-------------|
| **🏢 Fundamental** | 40% | P/E, EV/EBITDA, PEG, FCF Yield |
| **💎 Quality** | 25% | ROE, ROIC, Debt Ratios, Liquidity |
| **📈 Growth** | 20% | Revenue Growth, EPS Growth, Stability |
| **💭 Sentiment** | 15% | News + Reddit (Claude AI Analysis) |

**See:** [Methodology Guide](METHODS.md) for detailed algorithms

---

## 🏗️ System Architecture

### Data Flow:
```
1. COLLECT DATA
   Yahoo Finance + Reddit + News APIs
   ↓
2. PROCESS SENTIMENT
   Anthropic Batch API (50% cost savings)
   ↓
3. CALCULATE SCORES
   Multi-factor analysis
   ↓
4. VISUALIZE
   Interactive Streamlit Dashboard
```

### Key Components:
- **Data Collection:** `src/data/collectors.py`
- **Sentiment Analysis:** `src/data/sentiment_analyzer.py`
- **Score Calculation:** `src/calculations/`
- **Dashboard UI:** `analytics_dashboard.py`
- **API Key Management:** `src/utils/api_key_manager.py`

---

## 🔒 Security & Privacy

### API Key Storage:
- ✅ All keys stored in **macOS Keychain** (encrypted)
- ✅ No keys bundled in application
- ✅ Each user provides their own credentials
- ✅ Verified via automated security scans

### Data Privacy:
- ✅ All data stored locally (`~/.stockanalyzer/data/`)
- ✅ No data sent to third parties (except API providers)
- ✅ You control when data collection happens

---

## 📊 Current System Status

### Database Statistics:
- **503 stocks** tracked (S&P 500 universe)
- **47,727 news articles** with sentiment analysis
- **3,875 Reddit posts** with AI sentiment
- **51,602 total items** with sentiment scores
- **993 fundamental records** with financial metrics
- **125,756 price records** for technical analysis

### Test Coverage:
- ✅ **38/38 tests passing** (22 unit + 16 integration)
- ✅ Security compliance verified
- ✅ CI/CD pipeline tested

---

## 📚 Documentation

### For End Users:
- **[Installation Guide](docs/USER_INSTALLATION_GUIDE.md)** - Complete installation instructions
- **[Troubleshooting](docs/USER_INSTALLATION_GUIDE.md#troubleshooting)** - Common issues and solutions

### For Developers:
- **[Getting Started](docs/GETTING_STARTED.md)** - Development setup and workflow
- **[Build Guide](docs/BUILD_AND_DISTRIBUTE.md)** - Building and distribution
- **[CI/CD Usage](docs/CICD_USAGE.md)** - Automated pipeline guide
- **[CI/CD Quick Ref](docs/CICD_QUICK_REFERENCE.md)** - Quick reference card
- **[API Key Migration](docs/API_KEY_MIGRATION.md)** - Security architecture
- **[Implementation Roadmap](docs/IMPLEMENTATION_ROADMAP.md)** - Development phases

### For Contributors:
- **[CLAUDE.md](CLAUDE.md)** - AI assistant context and guidelines
- **[CHANGELOG.md](docs/CHANGELOG.md)** - Session history and changes
- **[METHODS.md](METHODS.md)** - Detailed scoring methodology

---

## 🛠️ Tech Stack

### Core Technologies:
- **Python 3.12** - Core language
- **Streamlit** - Dashboard framework
- **PyInstaller** - macOS app bundling
- **GitHub Actions** - CI/CD automation

### Data & APIs:
- **Yahoo Finance** - Stock fundamentals and prices
- **Reddit API** - Social sentiment (via PRAW)
- **Anthropic Claude** - AI sentiment analysis
- **SQLite** - Local data storage

### Security:
- **macOS Keychain** - Secure credential storage
- **Python Keyring** - Cross-platform key management

---

## 🚦 Quick Commands

### Development:
```bash
# Run dashboard
streamlit run analytics_dashboard.py

# Run tests
python -m pytest tests/ -v

# Collect data
python utilities/smart_refresh.py --data-types all

# Process sentiment
python utilities/smart_refresh.py --process-sentiment --poll
```

### Building:
```bash
# Build macOS app
pyinstaller StockAnalyzer.spec

# Create DMG
hdiutil create -volname "StockAnalyzer Pro" \
  -srcfolder dist/StockAnalyzer.app \
  -ov -format UDZO \
  StockAnalyzer-macOS-v1.0.0.dmg
```

### CI/CD:
```bash
# Promote to prod
gh workflow run promote-to-prod.yml -f version=v1.0.0

# Check build status
gh run list

# Download artifacts
gh run download
```

---

## 🗺️ Project Structure

```
stock-outlier/
├── .github/workflows/      # CI/CD pipelines
│   ├── test-on-main.yml
│   ├── promote-to-prod.yml
│   └── build-release.yml
├── src/
│   ├── calculations/       # Score calculation engines
│   ├── data/              # Data collection & storage
│   ├── ui/                # UI components
│   └── utils/             # Utilities (API key mgmt, etc.)
├── tests/                 # Test suite
├── utilities/             # CLI tools
├── docs/                  # Documentation
├── analytics_dashboard.py # Main dashboard
├── launcher_macos.py      # macOS launcher
├── StockAnalyzer.spec     # PyInstaller config
└── requirements.txt       # Python dependencies
```

---

## 🎯 Roadmap

### ✅ Phase 1: Core Functionality (COMPLETE)
- Multi-factor analysis
- Dashboard UI
- Data collection

### ✅ Phase 2: Security & Distribution (COMPLETE)
- API key management
- First-launch wizard
- macOS app bundling

### ✅ Phase 3-4: Build System (COMPLETE)
- PyInstaller configuration
- macOS launcher
- DMG creation

### ✅ Phase 5: CI/CD Pipeline (COMPLETE)
- Automated testing
- Automated builds
- GitHub Releases

### 🚧 Future Enhancements:
- Portfolio tracking
- Alerts and notifications
- Export to Excel/CSV
- Windows/Linux support

---

## 🐛 Known Issues

**None at this time** - All major issues resolved

Report issues at: [GitHub Issues](https://github.com/yourusername/stock-outlier/issues)

---

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

See [CLAUDE.md](CLAUDE.md) for development guidelines.

---

## 📄 License

Copyright © 2025. All rights reserved.

This software is provided as-is without warranty.

---

## 🙏 Acknowledgments

- **Anthropic** - Claude AI for sentiment analysis
- **Reddit** - Social sentiment data
- **Yahoo Finance** - Stock fundamentals and price data
- **Streamlit** - Dashboard framework
- **GitHub Actions** - CI/CD infrastructure

---

## 📞 Support

- **Documentation:** See [docs/](docs/) folder
- **Issues:** [GitHub Issues](https://github.com/yourusername/stock-outlier/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/stock-outlier/discussions)

---

**Latest Release:** [Download Now](https://github.com/yourusername/stock-outlier/releases/latest)

**Version:** 1.0.0 | **Platform:** macOS | **Last Updated:** November 20, 2025
