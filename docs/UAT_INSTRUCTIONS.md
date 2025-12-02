# User Acceptance Testing (UAT) Instructions

**StockAnalyzer Pro - Electron Migration**
**Date:** December 2, 2025
**Branch:** dev
**Version:** Post-Feature Implementation (HIGH + MEDIUM Priority)

---

## Prerequisites

Before starting UAT, ensure you have:
- Node.js v18+ installed (`node --version`)
- Python 3.11+ with virtual environment set up
- The `dev` branch checked out

---

## Quick Start

### Option 1: Using the Dev Script (Recommended)

```bash
cd /Users/sandeepmangaraj/myworkspace/Utilities/stock-outlier
./dev.sh
```

This will start both backend and frontend automatically.

### Option 2: Manual Start

**Terminal 1 - Start Backend:**
```bash
cd /Users/sandeepmangaraj/myworkspace/Utilities/stock-outlier
source venv/bin/activate
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 - Start Frontend:**
```bash
cd /Users/sandeepmangaraj/myworkspace/Utilities/stock-outlier/frontend
npm install  # First time only
npm run dev
```

---

## Access Points

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:5173 |
| **Backend API** | http://127.0.0.1:8000 |
| **API Documentation** | http://127.0.0.1:8000/api/docs |
| **Health Check** | http://127.0.0.1:8000/api/health |

---

## UAT Test Cases

### 1. Dashboard View (Home Page)

**URL:** http://localhost:5173/

**Test Steps:**
1. Open the frontend URL
2. Verify the sidebar appears on the left with navigation items
3. Check that the dashboard loads with:
   - [ ] Active stocks count (should be ~504)
   - [ ] Database size metric
   - [ ] Sectors count (should be ~12)
   - [ ] Last calculation date
4. Verify the sector distribution bar chart renders
5. Check the "Top Undervalued Stocks" list shows stocks with scores
6. Verify the "Data Tables" section shows record counts

**Expected Result:** Dashboard displays metrics, charts, and stock data correctly.

---

### 2. Weight Adjustment Sliders (NEW)

**Location:** Sidebar (below navigation)

**Test Steps:**
1. Look for the "Weight Adjustment" section in the sidebar
2. Verify four sliders are present:
   - [ ] Fundamental (default: 40%)
   - [ ] Quality (default: 25%)
   - [ ] Growth (default: 20%)
   - [ ] Sentiment (default: 15%)
3. Adjust the Fundamental slider to 60%
   - [ ] Normalized weights should update below the sliders
   - [ ] Reset button should appear
4. Click the reset button (circular arrow icon)
   - [ ] Weights should return to 40/25/20/15
   - [ ] Reset button should disappear
5. Adjust multiple sliders and verify normalization works
   - [ ] Normalized percentages should always sum to 100%

**Expected Result:** Sliders work, normalization is correct, reset button functions.

---

### 3. Stock Rankings View

**URL:** http://localhost:5173/rankings

**Test Steps:**
1. Navigate to Rankings from the sidebar
2. **Verify Top 5 Cards (NEW):**
   - [ ] "Top 5 Most Undervalued" card with stock cards
   - [ ] "Top 5 Most Overvalued" card with stock cards
   - [ ] Each card shows rank, symbol, company, sector, and score
   - [ ] Clicking a card navigates to Stock Analysis
3. Verify the rankings table loads with columns:
   - [ ] Rank, Symbol, Company, Sector
   - [ ] Original Score (composite)
   - [ ] Fundamental, Quality, Growth, Sentiment scores
   - [ ] Category badge
4. **Test Custom Weight Comparison (NEW):**
   - Adjust sidebar weights (e.g., set Sentiment to 50%)
   - [ ] Table should add "Custom" score column
   - [ ] Table should add "Δ Rank" column showing rank changes
   - [ ] "Biggest Movers" section should appear below Top 5 cards
   - [ ] Biggest Movers shows gainers (green) and losers (red)
5. Test search functionality:
   - [ ] Type "AAPL" in search box - should filter to Apple
   - [ ] Clear search - should show all stocks
6. Test category filter dropdown:
   - [ ] Select "Strong Undervalued" - should filter results
   - [ ] Select "All Categories" - should show all
7. Test sector filter dropdown:
   - [ ] Select "Technology" - should show only tech stocks
   - [ ] Select "All Sectors" - should show all
8. Click on column headers to verify sorting works
9. Click on a stock symbol (e.g., "AAPL") - should navigate to analysis

**Expected Result:** Top 5 cards display, custom weight comparison works, filters and sorting work.

---

### 4. Stock Analysis View

**URL:** http://localhost:5173/analysis?symbol=AAPL

**Test Steps:**
1. Navigate to Stock Analysis from sidebar
2. Enter "AAPL" in the search box and click "Analyze"
3. **Verify Stock Header:**
   - [ ] Symbol (AAPL)
   - [ ] Company name (Apple Inc.)
   - [ ] Sector and Industry
   - [ ] Composite/Custom score (changes based on weight adjustments)
   - [ ] Outlier category badge
4. **Check Score Cards with Weight Display (NEW):**
   - [ ] Fundamental Score shows current weight percentage
   - [ ] Quality Score shows current weight percentage
   - [ ] Growth Score shows current weight percentage
   - [ ] Sentiment Score shows current weight percentage
5. Verify the radar chart renders with all four components
6. Check the price history line chart shows 30 days of data
7. **Verify Historical Trends Charts (NEW):**
   - [ ] P/E Ratio trend chart
   - [ ] PEG Ratio trend chart
   - [ ] Composite Score trend chart
8. **Verify Investment Insights Section (NEW):**
   - [ ] "Strengths" card with green border (top 2 components)
   - [ ] "Areas for Attention" card with amber border (bottom components)
9. **Verify Metrics with Comparison (NEW):**
   - [ ] Expandable "Fundamental Metrics" section
   - [ ] Each metric shows current value, previous value, and trend arrow
   - [ ] Trend shows percentage change (green up, red down)
   - [ ] Expandable "Quality Metrics" section
   - [ ] Expandable "Growth Metrics" section
10. **Verify Peer Comparison (NEW):**
    - [ ] "Industry Peers" table shows stocks in same industry
    - [ ] "Sector Comparison" bar chart shows stock vs sector peers
    - [ ] Clicking a peer navigates to that stock's analysis
11. **Verify News & Reddit Sections (NEW):**
    - [ ] "Recent News" shows news articles with sentiment badges
    - [ ] Each article shows title, summary, publisher, date
    - [ ] Sentiment badges: Positive (green), Neutral (gray), Negative (red)
    - [ ] "Reddit Discussions" shows posts with sentiment badges
    - [ ] Each post shows title, subreddit, upvotes, comments
12. Verify the Sentiment Analysis summary section
13. Test with other symbols: MSFT, GOOGL, NVDA
14. Test with invalid symbol: "INVALID" - should show error

**Expected Result:** All new sections display correctly with data.

---

### 5. Data Management View

**URL:** http://localhost:5173/data

**Test Steps:**
1. Navigate to Data Management from sidebar
2. **Verify Data Source Status Section (NEW):**
   - [ ] Five data source cards displayed:
     - Fundamentals, Price Data, News Articles, Reddit Posts, Calculated Metrics
   - [ ] Each card shows record count
   - [ ] Each card shows freshness indicator:
     - Fresh (green) - recently updated
     - Aging (yellow) - needs refresh soon
     - Stale (red) - overdue for refresh
   - [ ] Color-coded left border matches freshness status
3. **Check Stale Data Warning (NEW):**
   - [ ] If any source is stale, warning banner appears at top right
4. Verify quick stats show:
   - [ ] Active Stocks count
   - [ ] Database Size
   - [ ] Pending Sentiment count
   - [ ] Last Calculation date
5. Check the three action cards are visible:
   - [ ] Data Refresh (blue)
   - [ ] Sentiment Analysis (purple)
   - [ ] Run Calculations (green)
6. **Verify Database Tables with Status Column (NEW):**
   - [ ] Table now includes "Status" column with freshness indicators
7. **Optional - Test Data Refresh:**
   - Click "Sync S&P 500 List" - should show status message
   - (Note: Full data refresh takes time, skip for quick UAT)
8. **Optional - Test Calculations:**
   - Click "Run Calculations" - should show progress

**Expected Result:** Data freshness indicators display correctly, all features work.

---

### 6. Navigation & UI

**Test Steps:**
1. Click each sidebar navigation item:
   - [ ] Dashboard - loads dashboard
   - [ ] Rankings - loads rankings table
   - [ ] Stock Analysis - loads analysis view
   - [ ] Data Management - loads data management
2. Click "Strong Undervalued" quick filter - navigates to filtered rankings
3. Click "Strong Overvalued" quick filter - navigates to filtered rankings
4. **Test Weight Persistence:**
   - [ ] Adjust weights on one page
   - [ ] Navigate to another page
   - [ ] Weights should persist across pages
5. Verify responsive behavior:
   - [ ] Resize browser window
   - [ ] Content should remain readable

**Expected Result:** All navigation works, weights persist, UI is responsive.

---

### 7. API Verification (Optional)

Open http://127.0.0.1:8000/api/docs in browser

**Test Steps:**
1. Expand "GET /api/health" and click "Try it out" → "Execute"
   - [ ] Should return `{"status": "healthy", "database_connected": true}`
2. Expand "GET /api/stocks" and execute
   - [ ] Should return list of stocks
3. Expand "GET /api/stocks/{symbol}" with "AAPL" and execute
   - [ ] Should return Apple stock details with scores
4. **Test Extended Stock Endpoint (NEW):**
   - Expand "GET /api/stocks/{symbol}/extended" with "AAPL"
   - [ ] Should return extended data including:
     - `news_articles` array
     - `reddit_posts` array
     - `historical_metrics` array
     - `industry_peers` array
     - `sector_peers` array
     - `insights` object with strengths and weaknesses
     - `fundamentals` with `_prev` fields for comparison
5. Expand "GET /api/rankings" and execute
   - [ ] Should return rankings list

**Expected Result:** All API endpoints respond with correct data.

---

## New Features Summary

| Feature | Location | Status |
|---------|----------|--------|
| Weight Adjustment Sliders | Sidebar | NEW |
| Top 5 Undervalued/Overvalued Cards | Rankings | NEW |
| Custom Weight Score Comparison | Rankings Table | NEW |
| Biggest Movers Section | Rankings | NEW |
| Current vs Previous Metrics | Stock Analysis | NEW |
| Historical Trend Charts | Stock Analysis | NEW |
| Investment Insights | Stock Analysis | NEW |
| News Articles with Sentiment | Stock Analysis | NEW |
| Reddit Posts with Sentiment | Stock Analysis | NEW |
| Industry Peer Comparison | Stock Analysis | NEW |
| Sector Comparison Chart | Stock Analysis | NEW |
| Data Source Freshness Indicators | Data Management | NEW |
| Extended Stock API Endpoint | Backend | NEW |

---

## Known Limitations (Phase 4)

1. **Electron app not yet packaged** - Running in browser mode only
2. **No Python bundling** - Requires local Python installation
3. **No auto-update** - Will be added in Phase 5
4. **WebSocket progress updates** - Not yet connected to UI

---

## Reporting Issues

If you find any issues during UAT, please note:
1. **Which test case failed**
2. **Steps to reproduce**
3. **Expected vs Actual behavior**
4. **Browser console errors** (F12 → Console tab)
5. **Backend logs** (Terminal running uvicorn)

---

## Stopping the Servers

- If using `./dev.sh`: Press `Ctrl+C`
- If manual: Press `Ctrl+C` in each terminal

---

## Quick Verification Commands

```bash
# Check backend health
curl http://127.0.0.1:8000/api/health

# Get stock count
curl "http://127.0.0.1:8000/api/stocks?limit=1" | jq '.total'

# Get AAPL details
curl http://127.0.0.1:8000/api/stocks/AAPL | jq '.scores.composite_score'

# Get AAPL extended details (NEW)
curl http://127.0.0.1:8000/api/stocks/AAPL/extended | jq '.news_articles | length'

# Get rankings count
curl "http://127.0.0.1:8000/api/rankings?limit=1" | jq '.total'
```

---

## Sign-Off

After completing UAT, please confirm:

- [ ] Dashboard displays correctly
- [ ] **Weight adjustment sliders work (NEW)**
- [ ] Rankings table works with filtering/sorting
- [ ] **Top 5 cards and Biggest Movers work (NEW)**
- [ ] **Custom weight comparison works (NEW)**
- [ ] Stock analysis shows details and charts
- [ ] **Historical trends, peer comparison, news/Reddit display (NEW)**
- [ ] **Investment insights display (NEW)**
- [ ] Data management interface functional
- [ ] **Data freshness indicators work (NEW)**
- [ ] Navigation works throughout app
- [ ] No critical errors in browser console
- [ ] Ready to proceed to Phase 5 (Packaging)

**Tester:** _______________
**Date:** _______________
**Status:** [ ] PASS / [ ] FAIL with issues

**Notes:**
_____________________________________________
_____________________________________________
_____________________________________________
