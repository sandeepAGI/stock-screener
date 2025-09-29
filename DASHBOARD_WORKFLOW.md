# Unified Dashboard Workflow - StockAnalyzer Pro

## 🎯 Streamlined 3-Step Process

### Step 1: 📥 Collect Raw Data
**Purpose:** Gather latest market data WITHOUT calculating sentiment
- **Fundamentals:** Financial metrics from Yahoo Finance
- **Prices:** Historical price data for technical analysis
- **News:** Articles and headlines (sentiment_score = NULL)
- **Reddit:** Social media posts (sentiment_score = NULL)

**Actions:**
- Quick Refresh (all data types for selected stocks)
- Manual Refresh (specific data types)
- Smart Refresh (automatically determines what's stale)

### Step 2: 🤖 Process Sentiment via Claude API
**Purpose:** Calculate high-quality sentiment scores using bulk API
- **Batch Submission:** Send up to 100,000 items per batch
- **Cost Savings:** 50% cheaper than individual API calls
- **Processing Time:** Typically completes in <1 hour
- **Quality:** Claude's superior financial context understanding

**Actions:**
1. Check if any items need sentiment (NULL sentiment_score)
2. Submit batch to Anthropic API
3. Monitor batch status
4. Retrieve results when complete
5. Update database with sentiment scores

### Step 3: 📊 Calculate Final Scores
**Purpose:** Generate composite rankings using ALL data
- **Uses existing sentiment scores** (no recalculation!)
- **Combines 4 components:** Fundamental (40%), Quality (25%), Growth (20%), Sentiment (15%)
- **Outputs:** Final stock rankings and recommendations

**Actions:**
- Run after sentiment processing completes
- Updates calculated_metrics table
- Refreshes dashboard visualizations

## 🔄 Data Flow

```
1. COLLECT
   Yahoo Finance → [fundamentals, prices] → Database (raw data)
   News API      → [articles]             → Database (sentiment_score = NULL)
   Reddit API    → [posts]                → Database (sentiment_score = NULL)

2. PROCESS SENTIMENT
   Database → Batch Processor → Claude API → sentiment_score updated

3. CALCULATE SCORES
   Database (with sentiment) → Calculators → Composite Scores → Rankings
```

## ⚠️ Critical Changes Made

### Fixed: SentimentCalculator Now Uses Existing Scores
**Before:** Step 3 would recalculate sentiment using TextBlob/VADER (ignoring Claude API results)
**After:** Step 3 reads sentiment_score column directly from database

**Modified Files:**
- `src/calculations/sentiment.py`
  - `calculate_news_sentiment()` - Now reads sentiment_score column
  - `calculate_social_sentiment()` - Now reads sentiment_score column
  - `calculate_sentiment_momentum()` - Now reads sentiment_score column

### Why This Matters:
1. **No wasted API calls** - Claude sentiment is used, not discarded
2. **Consistent quality** - Claude's financial understanding throughout
3. **Clear workflow** - Each step has distinct purpose
4. **Cost effective** - Bulk API pricing, no redundant processing

## 📋 Dashboard UI Reorganization Needed

### Current Issues:
- Steps 1, 2, 3 mixed with bulk processing section
- Unclear when to use which feature
- Confusing flow for users

### Proposed Structure:
```
Data Management Tab
├── Step 1: Collect Data
│   ├── Quick Refresh (all types)
│   └── Advanced Options (selective)
├── Step 2: Process Sentiment
│   ├── Check Status (items needing sentiment)
│   ├── Submit Batch
│   └── Monitor/Retrieve Results
└── Step 3: Calculate Rankings
    └── Update Composite Scores button
```

## ✅ Implementation Status

- [x] Modified SentimentCalculator to use existing scores
- [x] Fixed database schema issues
- [x] Created batch processing workflow
- [ ] Reorganize dashboard UI for clarity
- [ ] Add clear status indicators for each step
- [ ] Add validation to prevent Step 3 before Step 2 completes