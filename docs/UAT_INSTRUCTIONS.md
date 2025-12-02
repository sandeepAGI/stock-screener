# User Acceptance Testing (UAT) Instructions

**StockAnalyzer Pro - Electron Migration**
**Date:** December 1, 2025
**Branch:** dev

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

### 2. Stock Rankings View

**URL:** http://localhost:5173/rankings

**Test Steps:**
1. Navigate to Rankings from the sidebar
2. Verify the rankings table loads with columns:
   - [ ] Rank, Symbol, Company, Sector
   - [ ] Composite, Fundamental, Quality, Growth, Sentiment scores
   - [ ] Category badge
3. Test search functionality:
   - [ ] Type "AAPL" in search box - should filter to Apple
   - [ ] Clear search - should show all stocks
4. Test category filter dropdown:
   - [ ] Select "Strong Undervalued" - should filter results
   - [ ] Select "All Categories" - should show all
5. Test sector filter dropdown:
   - [ ] Select "Technology" - should show only tech stocks
   - [ ] Select "All Sectors" - should show all
6. Click on column headers to verify sorting works
7. Click on a stock symbol (e.g., "AAPL") - should navigate to analysis

**Expected Result:** Table displays, filters work, sorting works, navigation works.

---

### 3. Stock Analysis View

**URL:** http://localhost:5173/analysis?symbol=AAPL

**Test Steps:**
1. Navigate to Stock Analysis from sidebar
2. Enter "AAPL" in the search box and click "Analyze"
3. Verify the stock header shows:
   - [ ] Symbol (AAPL)
   - [ ] Company name (Apple Inc.)
   - [ ] Sector and Industry
   - [ ] Composite score
   - [ ] Outlier category badge
4. Check the four score cards display:
   - [ ] Fundamental Score (40% weight)
   - [ ] Quality Score (25% weight)
   - [ ] Growth Score (20% weight)
   - [ ] Sentiment Score (15% weight)
5. Verify the radar chart renders with all four components
6. Check the price history line chart shows 30 days of data
7. Verify the Key Fundamentals section shows metrics:
   - [ ] P/E Ratio, Forward P/E, PEG, P/B
   - [ ] ROE, Debt/Equity, Revenue Growth, etc.
8. Check the Sentiment Analysis section (if available)
9. Test with other symbols: MSFT, GOOGL, NVDA
10. Test with invalid symbol: "INVALID" - should show error

**Expected Result:** Stock details, scores, charts, and fundamentals display correctly.

---

### 4. Data Management View

**URL:** http://localhost:5173/data

**Test Steps:**
1. Navigate to Data Management from sidebar
2. Verify quick stats show:
   - [ ] Active Stocks count
   - [ ] Database Size
   - [ ] Pending Sentiment count
   - [ ] Last Calculation date
3. Check the three action cards are visible:
   - [ ] Data Refresh (blue)
   - [ ] Sentiment Analysis (purple)
   - [ ] Run Calculations (green)
4. Verify the Database Tables section shows all tables with record counts
5. **Optional - Test Data Refresh:**
   - Click "Sync S&P 500 List" - should show status message
   - (Note: Full data refresh takes time, skip for quick UAT)
6. **Optional - Test Calculations:**
   - Click "Run Calculations" - should show progress

**Expected Result:** Data management interface displays correctly, actions trigger operations.

---

### 5. Navigation & UI

**Test Steps:**
1. Click each sidebar navigation item:
   - [ ] Dashboard - loads dashboard
   - [ ] Rankings - loads rankings table
   - [ ] Stock Analysis - loads analysis view
   - [ ] Data Management - loads data management
2. Click "Strong Undervalued" quick filter - navigates to filtered rankings
3. Click "Strong Overvalued" quick filter - navigates to filtered rankings
4. Verify responsive behavior:
   - [ ] Resize browser window
   - [ ] Content should remain readable

**Expected Result:** All navigation works, UI is responsive.

---

### 6. API Verification (Optional)

Open http://127.0.0.1:8000/api/docs in browser

**Test Steps:**
1. Expand "GET /api/health" and click "Try it out" → "Execute"
   - [ ] Should return `{"status": "healthy", "database_connected": true}`
2. Expand "GET /api/stocks" and execute
   - [ ] Should return list of stocks
3. Expand "GET /api/stocks/{symbol}" with "AAPL" and execute
   - [ ] Should return Apple stock details with scores
4. Expand "GET /api/rankings" and execute
   - [ ] Should return rankings list

**Expected Result:** All API endpoints respond with correct data.

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

# Get rankings count
curl "http://127.0.0.1:8000/api/rankings?limit=1" | jq '.total'
```

---

## Sign-Off

After completing UAT, please confirm:

- [ ] Dashboard displays correctly
- [ ] Rankings table works with filtering/sorting
- [ ] Stock analysis shows details and charts
- [ ] Data management interface functional
- [ ] Navigation works throughout app
- [ ] No critical errors in browser console
- [ ] Ready to proceed to Phase 5 (Packaging)

**Tester:** _______________
**Date:** _______________
**Status:** [ ] PASS / [ ] FAIL with issues
