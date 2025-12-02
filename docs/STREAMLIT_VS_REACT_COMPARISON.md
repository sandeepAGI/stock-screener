# Streamlit vs React Frontend Comparison

**Purpose:** Document differences between the original Streamlit dashboard and the new React frontend to identify what was intentional vs. oversight.

---

## Summary

| Category | Status |
|----------|--------|
| **Missing (Oversight)** | 8 features |
| **Missing (Intentional)** | 2 features |
| **Simplified** | 4 features |
| **Equivalent** | 6 features |

---

## 1. Rankings Tab (Streamlit) vs Rankings Page (React)

### Streamlit Features:
- Top 5 Most Undervalued stocks list with detailed cards
- Top 5 Most Overvalued stocks list with detailed cards
- **Custom weight sliders** in sidebar (40/25/20/15 adjustable)
- Side-by-side comparison: Original vs Custom rankings
- "Biggest Movers" section showing rank changes
- Sector and market cap in stock cards
- Score and rank displayed per stock

### React Features:
- Full rankings table with all columns
- Search filter
- Category filter dropdown
- Sector filter dropdown
- Sortable columns
- Click to navigate to analysis

### **Missing (Oversight):**
| Feature | Priority | Notes |
|---------|----------|-------|
| **Weight adjustment sliders** | HIGH | Core feature - lets users customize weights (40/25/20/15) |
| **Side-by-side original vs custom rankings** | HIGH | Shows how custom weights affect rankings |
| **"Biggest Movers" section** | MEDIUM | Shows stocks that gain/lose most with weight changes |
| **Top 5 Undervalued/Overvalued cards** | MEDIUM | Visual summary at top of page |

---

## 2. Individual Stock Analysis Tab (Streamlit) vs Stock Analysis Page (React)

### Streamlit Features:
- Stock search with dropdown (sorted by score)
- Quick search text input with filtering
- **Component Score Overview** with radar chart (Plotly)
- **Underlying Metrics Breakdown** with 4 expandable sections:
  - Fundamental Metrics (P/E, Forward P/E, PEG, P/B) with current vs previous
  - Quality Metrics (ROE, Debt/Equity, Current Ratio) with current vs previous
  - Growth Metrics (Revenue Growth, EPS Growth) with current vs previous
  - Sentiment Metrics (News avg, Reddit avg with article counts)
- **Historical Trends** (3 line charts):
  - P/E Ratio trend
  - PEG Ratio trend
  - Composite Score trend
- **Recent News & Sentiment** expandables:
  - News articles with sentiment (positive/neutral/negative counts)
  - Reddit discussions with sentiment
- **Peer Comparison**:
  - Industry peers table (direct competitors)
  - Sector peers table + bar chart
- **Investment Insights**:
  - Strengths section (top 2 components)
  - Areas for Attention section (bottom components)

### React Features:
- Stock search input
- Basic header with symbol, company, sector
- Composite score display
- 4 score cards (Fundamental, Quality, Growth, Sentiment)
- Radar chart (Recharts)
- Price history line chart (30 days)
- Key Fundamentals grid (12 metrics)
- Sentiment section (basic)

### **Missing (Oversight):**
| Feature | Priority | Notes |
|---------|----------|-------|
| **Metrics with current vs previous comparison** | HIGH | Shows trend direction for each metric |
| **Historical Trends charts** | HIGH | P/E, PEG, Composite score over time |
| **News articles list with sentiment** | HIGH | Shows actual headlines with sentiment scores |
| **Reddit discussions list** | MEDIUM | Shows Reddit posts with sentiment |
| **Peer Comparison tables** | HIGH | Industry & sector competitors with scores |
| **Peer Comparison bar chart** | MEDIUM | Visual vs sector average |
| **Investment Insights section** | MEDIUM | Strengths & areas for attention |
| **Expandable metric sections** | LOW | Collapsible detail sections |

---

## 3. Data Management Tab (Streamlit) vs Data Management Page (React)

### Streamlit Features:
- **Data Source Status Table** with:
  - Source name, Record count, Last update, Status (🟢/🟡/🔴), Days old
- **Data Collection Actions**:
  - Refresh All (with confirmation)
  - Refresh by symbol input
  - Refresh by data type checkboxes
  - Force refresh toggle
- **Stock Universe Management**:
  - Sync S&P 500 button
  - Add custom symbol input
- **Sentiment Processing**:
  - Submit new batch button
  - View pending items count
  - Active batches list with status
- **Calculation Actions**:
  - Recalculate All button
  - Recalculate specific symbols
- **Database Statistics**:
  - Full table with all database tables
  - Size, row counts, etc.

### React Features:
- Quick stats cards (Active stocks, DB size, Pending sentiment, Last calculation)
- Progress bar during collection
- Three action cards:
  - Data Refresh (Refresh All, Sync S&P 500)
  - Sentiment Analysis (Process Sentiment)
  - Run Calculations
- Database Tables list with record counts

### **Missing (Oversight):**
| Feature | Priority | Notes |
|---------|----------|-------|
| **Data source freshness status (🟢/🟡/🔴)** | MEDIUM | Visual indicator per data type |
| **Refresh by specific symbols** | MEDIUM | Text input for specific stocks |
| **Refresh by data type selection** | LOW | Checkboxes for fundamentals/prices/news/reddit |
| **Active batches list** | LOW | Show pending sentiment batches |

### **Simplified (Intentional):**
- Combined multiple refresh options into single "Refresh All" button
- Removed force refresh toggle (always smart refresh)

---

## 4. Methodology Tab (Streamlit) vs (Not in React)

### Streamlit Features:
- Full methodology documentation page with:
  - Overview of 4-component system
  - Detailed explanation of each component
  - Scoring interpretation guide
  - Advanced features explanation
  - Risk and limitations
  - Version history

### React Status:
- **NOT IMPLEMENTED**

### **Missing (Intentional - for now):**
| Feature | Priority | Notes |
|---------|----------|-------|
| Methodology Guide page | LOW | Can be added later as /methodology route |

---

## 5. Sidebar Features (Streamlit) vs Sidebar (React)

### Streamlit Features:
- Logo/branding
- **Weight adjustment sliders** (Fundamental, Quality, Growth, Sentiment)
- Database stats summary
- Last calculation date
- Reset to default weights button

### React Features:
- Logo/branding
- Navigation links
- Quick filters (Strong Undervalued, Strong Overvalued)
- Version number

### **Missing (Oversight):**
| Feature | Priority | Notes |
|---------|----------|-------|
| **Weight adjustment sliders** | HIGH | Key interactive feature |
| **Reset weights button** | MEDIUM | Reset to 40/25/20/15 defaults |

---

## 6. Dashboard Page (React only - NEW)

### React Features (Not in Streamlit):
- Overview metrics cards
- Sector distribution bar chart
- Top undervalued stocks list
- Data tables summary

### Status:
- **NEW FEATURE** - This is a React addition, not in Streamlit
- Streamlit uses tabs; React uses separate pages with a dashboard home

---

## Priority Summary

### HIGH Priority Missing Features (Should Add Before UAT):
1. **Weight adjustment sliders** - Core feature for customizing methodology
2. **Current vs Previous metric comparison** - Shows trend direction
3. **Historical trend charts** - P/E, PEG, Composite over time
4. **News/Reddit articles list** - Actual content with sentiment
5. **Peer comparison tables** - Industry and sector competitors

### MEDIUM Priority (Nice to Have):
1. Top 5 Undervalued/Overvalued summary cards
2. "Biggest Movers" with weight changes
3. Investment Insights (Strengths/Weaknesses)
4. Data source freshness indicators
5. Refresh by specific symbols

### LOW Priority (Can Add Later):
1. Methodology guide page
2. Expandable metric sections
3. Active batches list
4. Refresh by data type selection

---

## Recommendation

Before proceeding with UAT and Phase 5, I recommend adding at minimum:

1. **Weight adjustment sliders** in the sidebar or a settings panel
2. **Peer comparison section** in Stock Analysis
3. **News headlines list** in Stock Analysis
4. **Historical trend charts** in Stock Analysis

These are the features most likely to be noticed as "missing" by users familiar with the Streamlit version.

Would you like me to implement these before UAT?
