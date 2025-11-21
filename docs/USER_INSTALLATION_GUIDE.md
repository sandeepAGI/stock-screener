# StockAnalyzer Pro - Installation Guide

**Version:** 1.0.0
**Platform:** macOS (Intel & Apple Silicon)
**Last Updated:** November 20, 2025

---

## 📋 Overview

StockAnalyzer Pro is a comprehensive stock analysis tool that helps you identify undervalued and overvalued stocks in the S&P 500 using advanced sentiment analysis and fundamental metrics.

### ✨ Key Features:
- 📊 Multi-factor stock scoring (Fundamental, Quality, Growth, Sentiment)
- 🤖 AI-powered sentiment analysis using Claude
- 📱 Social media sentiment tracking via Reddit
- 📈 Interactive visualizations and rankings
- 🔐 Secure API key storage in macOS Keychain

---

## 💻 System Requirements

### Minimum Requirements:
- **OS:** macOS 10.13 (High Sierra) or later
- **RAM:** 4 GB (8 GB recommended)
- **Disk Space:** 500 MB free space
- **Internet:** Required for data collection and analysis

### Recommended:
- **OS:** macOS 12 (Monterey) or later
- **RAM:** 8 GB or more
- **Disk Space:** 1 GB free space
- **Display:** 1920x1080 or higher resolution

---

## 📥 Installation

### Option 1: Download Pre-Built Application (Recommended)

1. **Download** the latest release from GitHub:
   - Go to: [GitHub Releases](https://github.com/yourusername/stock-outlier/releases)
   - Download: `StockAnalyzer-macOS-v1.0.0.dmg`

2. **Open** the downloaded `.dmg` file

3. **Drag** `StockAnalyzer.app` to your Applications folder

4. **First Launch:**
   - Right-click (or Control-click) on `StockAnalyzer.app`
   - Select "Open" from the menu
   - Click "Open" in the security dialog
   - (This is required for unsigned applications on macOS)

### Option 2: Build from Source

If you prefer to build from source:

```bash
# Clone the repository
git checkout prod
cd stock-outlier

# Install dependencies
pip install -r requirements.txt

# Build the application
pyinstaller StockAnalyzer.spec

# The app will be in dist/StockAnalyzer.app
```

---

## 🔑 Initial Setup

### First Launch Wizard

When you launch StockAnalyzer Pro for the first time, you'll see a setup wizard that guides you through configuring your API credentials.

### Required API Keys:

#### 1. Reddit API (FREE)
**Purpose:** Collect social media sentiment data
**Cost:** Free
**Time to setup:** ~5 minutes

**Steps:**
1. Visit: https://www.reddit.com/prefs/apps
2. Log in to your Reddit account (or create one)
3. Click "create another app..."
4. Fill in:
   - **name:** `StockAnalyzer`
   - **type:** Select "script"
   - **redirect uri:** `http://localhost:8080`
5. Click "create app"
6. Copy your credentials:
   - **Client ID:** (14 characters under app name)
   - **Client Secret:** (27 characters, click "show")

#### 2. Claude API (PAID)
**Purpose:** Advanced AI-powered sentiment analysis
**Cost:** Usage-based (you choose what to process)
**Time to setup:** ~5 minutes

**Steps:**
1. Visit: https://console.anthropic.com/
2. Sign up for an account
3. Add credits to your account (start with $5-10)
4. Navigate to "API Keys" section
5. Click "Create Key"
6. Name it: `StockAnalyzer`
7. Copy the key (starts with `sk-ant-api03-`)

### Cost Information:

| Usage Type | Typical Cost |
|------------|---------------|
| Small portfolio (10-20 stocks) | $1-5 initial setup |
| Monthly updates (new articles only) | Cents to a few dollars |
| Reddit sentiment collection | FREE |
| **You control:** | Process only what you need |

**How it works:**
- 50% discount via Anthropic's Batch API
- You manually submit batches for processing
- Choose date ranges and stocks to analyze
- No automatic charges

💡 **Tip:** Start with a small portfolio to test costs before analyzing the full S&P 500.

---

## 🚀 Getting Started

### 1. Launch the Application

Double-click `StockAnalyzer.app` in your Applications folder.

### 2. Complete the Setup Wizard

Follow the on-screen instructions to enter your API credentials:
- Enter Reddit credentials (Tab 1)
- Enter Claude API key (Tab 2)
- Complete setup (Tab 3)

### 3. Start Analysis

Once setup is complete, you can:
- View stock rankings
- Analyze individual stocks
- Collect fresh data
- Run sentiment analysis

---

## 📊 Using StockAnalyzer Pro

### Main Dashboard Tabs:

#### 📈 Rankings
- View top undervalued and overvalued stocks
- Filter by sector, market cap, and quality thresholds
- Adjust scoring weights in real-time
- Export rankings to CSV

#### 📊 Individual Analysis
- Deep dive into specific stocks
- View detailed metrics breakdown
- See sentiment analysis results
- Compare against sector averages

#### 🗄️ Data Management
- Collect fresh data for stocks
- Run sentiment analysis batches
- Monitor batch processing status
- View data coverage statistics

#### ⚙️ API Settings
- Update API credentials
- Test API connections
- View API status
- Manage stored credentials

### Workflow Example:

1. **Initial Data Collection** (1-2 hours)
   ```
   Data Management → Collect Data → Select All Stocks
   ```

2. **Run Sentiment Analysis** (30-60 minutes)
   ```
   Data Management → Process Sentiment → Submit Batch
   ```

3. **View Results**
   ```
   Rankings → Top 20 Undervalued Stocks
   ```

4. **Deep Dive**
   ```
   Individual Analysis → Search for stock symbol
   ```

---

## 🔒 Security & Privacy

### API Key Storage:
- All API keys are stored securely in macOS Keychain
- Keys are encrypted by the operating system
- No API keys are stored in plain text files
- Each user's keys are isolated

### Data Storage:
- Stock data is stored locally in: `~/.stockanalyzer/data/`
- No data is sent to third parties (except API providers)
- You control when data collection happens

### Network Activity:
- Reddit API: For social sentiment collection
- Claude API: For sentiment analysis
- Yahoo Finance: For stock fundamentals and price data

---

## 🐛 Troubleshooting

### Application Won't Open

**Problem:** "StockAnalyzer.app is damaged and can't be opened"

**Solution:**
1. Right-click the app
2. Select "Open"
3. Click "Open" in the security dialog
4. If that doesn't work, try:
   ```bash
   xattr -cr /Applications/StockAnalyzer.app
   ```

### API Connection Failed

**Problem:** "Reddit API connection failed"

**Solution:**
1. Go to API Settings tab
2. Click "Test Connection"
3. Verify credentials are correct
4. Check that you created a "script" type app (not "web app")

**Problem:** "Claude API connection failed"

**Solution:**
1. Verify you have credits in your Anthropic account
2. Check that the API key starts with `sk-ant-api03-`
3. Ensure you copied the entire key (they're quite long)

### Port Already in Use

**Problem:** "Could not find available port"

**Solution:**
1. Close other applications using ports 8501-8510
2. Restart StockAnalyzer Pro
3. The launcher will automatically find an available port

### Data Not Loading

**Problem:** "No data available"

**Solution:**
1. Go to Data Management tab
2. Click "Collect Data"
3. Select stocks to collect data for
4. Wait for collection to complete (check progress bar)

---

## 📞 Support

### Getting Help:
- **Issues:** https://github.com/yourusername/stock-outlier/issues
- **Discussions:** https://github.com/yourusername/stock-outlier/discussions
- **Email:** support@stockanalyzer.com (if applicable)

### Before Reporting an Issue:
1. Check this troubleshooting guide
2. Verify your API credentials are correct
3. Check your internet connection
4. Try restarting the application
5. Include error messages and screenshots when reporting

---

## 🔄 Updating

### Automatic Updates (Future):
Automatic update checking is planned for future releases.

### Manual Updates:
1. Download the latest version
2. Quit StockAnalyzer Pro
3. Replace the old app in Applications with the new one
4. Launch the new version
5. Your data and API keys will be preserved

---

## 🗑️ Uninstallation

To completely remove StockAnalyzer Pro:

1. **Delete the Application:**
   ```bash
   rm -rf /Applications/StockAnalyzer.app
   ```

2. **Delete User Data** (optional):
   ```bash
   rm -rf ~/.stockanalyzer
   ```

3. **Remove API Keys from Keychain** (optional):
   - Open Keychain Access app
   - Search for "StockAnalyzer-Pro"
   - Delete all entries

---

## 📝 License

Copyright © 2025. All rights reserved.

This software is provided as-is without warranty. Use at your own risk.

---

## 🙏 Acknowledgments

- **Anthropic** - Claude AI for sentiment analysis
- **Reddit** - Social sentiment data
- **Yahoo Finance** - Stock fundamentals and price data
- **Streamlit** - Dashboard framework

---

**Version:** 1.0.0
**Last Updated:** November 20, 2025
**Platform:** macOS

For the latest documentation, visit: https://github.com/yourusername/stock-outlier
