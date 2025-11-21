# StockAnalyzer Pro - Development Guide for Claude
**Last Updated:** November 20, 2025 (Late Session)
**Purpose:** Quick reference for AI assistant working on this codebase

---

## 📚 Documentation Maintenance Guidelines

### **CRITICAL: When to Update This File**

This file (CLAUDE.md) should be updated ONLY when:
- ✅ System architecture changes (new tables, major refactoring)
- ✅ Database statistics change significantly (major data collection)
- ✅ Working components list changes (new features added/removed)
- ✅ Current priorities shift (new phase of development)
- ✅ Development guidelines change (new working principles)
- ✅ Configuration requirements change (new API keys, settings)

**DO NOT update this file for:**
- ❌ Session accomplishments (use `docs/CHANGELOG.md` instead)
- ❌ Bug fixes (use `docs/CHANGELOG.md` instead)
- ❌ Minor improvements or tweaks
- ❌ Temporary work-in-progress notes

### **Update Workflow:**

**At End of Each Session:**
```
1. Add session accomplishments to docs/CHANGELOG.md
   - What was done
   - Problems encountered
   - Solutions implemented
   - Files modified
   - Results achieved

2. Update CLAUDE.md ONLY IF system state changed
   - New architecture components?
   - Database schema changes?
   - New working principles?
   - Changed priorities?

3. Update "Last Updated" date at top of this file
```

### **File Ownership:**

| File | Purpose | Update Frequency | Content Type |
|------|---------|------------------|--------------|
| **CLAUDE.md** | Current state reference | When system changes | Current state only |
| **docs/CHANGELOG.md** | Historical record | After every session | Detailed history |
| **README.md** | User documentation | When features change | User-facing info |
| **docs/IMPLEMENTATION_ROADMAP.md** | Project plans | When planning | Future plans |

### **Example Session Close:**

**✅ CORRECT:**
```markdown
# Session close:
1. Update docs/CHANGELOG.md with today's work:
   - Fixed Reddit validation bug
   - Implemented tiered validation logic
   - Cleaned up 860 false positives

2. CLAUDE.md stays unchanged (system architecture didn't change)

3. Commit both:
   git add docs/CHANGELOG.md
   git commit -m "docs: Add Nov 20 session to changelog"
```

**❌ INCORRECT:**
```markdown
# Session close:
1. Add 150 lines to CLAUDE.md describing today's session
2. CLAUDE.md now 1,100 lines and hard to read
3. Next session Claude spends 5 minutes reading old session notes
```

### **Keep This File Focused:**

**Target Size:** 200-350 lines (currently ~250)
**Reading Time:** 2-3 minutes for Claude to absorb
**Purpose:** Quick context about current state, not historical archive

If this file grows beyond 400 lines, it's time to audit and move historical content to CHANGELOG.md.

---

## 🎯 Current System State

### **Database Status**
- **503 stocks** tracked in S&P 500 universe (511 total, 8 inactive)
- **47,727 news articles** with sentiment analysis (100% coverage)
- **3,875 Reddit posts** with Claude LLM sentiment (100% coverage)
- **51,602 total items** with complete sentiment scores
- **993 fundamental records** with complete financial metrics
- **125,756 price records** for technical analysis

### **Working Components**
- ✅ Data collection (Yahoo Finance, Reddit, News)
- ✅ Bulk sentiment processing (Anthropic Batch API)
- ✅ All 4 calculators (Fundamental, Quality, Growth, Sentiment)
- ✅ Composite scoring (40/25/20/15 weighting)
- ✅ Dashboard UI (`analytics_dashboard.py`) with first-launch wizard
- ✅ CLI tools (`smart_refresh.py`, `batch_monitor.py`)
- ✅ API Key Manager (macOS Keychain integration)
- ✅ macOS application bundling (PyInstaller)
- ✅ CI/CD pipeline (GitHub Actions, automated builds & releases)
- ✅ Complete test suite (38 tests: 22 unit + 16 integration)

### **Current Issues**
- Dashboard fragmentation: `streamlit_app.py` vs `analytics_dashboard.py` (low priority)

---

## 🏗️ System Architecture

### **Data Flow**
```
Step 1: COLLECT DATA
Yahoo Finance ─┐
News APIs ─────┼─→ DataCollectionOrchestrator ─→ SQLite (sentiment_score=NULL)
Reddit API ────┘

Step 2: PROCESS SENTIMENT
Database ─→ UnifiedBulkProcessor ─→ Anthropic Batch API ─→ Update sentiment_score

Step 3: CALCULATE RANKINGS
Database (with sentiment) ─→ Calculators ─→ Composite Scores ─→ Dashboard
```

### **Key Database Tables**
- `stocks` - S&P 500 constituent tracking (is_active flag for delisted)
- `fundamental_data` - Financial metrics from Yahoo Finance
- `price_data` - Historical price data
- `news_articles` - News with sentiment_score
- `reddit_posts` - Reddit posts with sentiment_score
- `calculated_metrics` - Final composite scores
- `batches` - Batch processing status
- `batch_mapping` - Maps batch IDs to record IDs (PRIMARY tracking)
- `temp_sentiment_queue` - Alternative path for sentiment processing

### **Project Structure**
```
stock-outlier/
├── .github/
│   └── workflows/              # CI/CD pipelines
│       ├── test-on-main.yml
│       ├── promote-to-prod.yml
│       └── build-release.yml
├── src/
│   ├── calculations/           # Score calculation engines
│   ├── data/                   # Data collection and storage
│   │   ├── collectors.py       # DataCollectionOrchestrator
│   │   ├── sentiment_analyzer.py
│   │   ├── unified_bulk_processor.py
│   │   └── database.py
│   ├── ui/                     # UI components
│   │   ├── __init__.py
│   │   └── api_config_ui.py   # First-launch wizard
│   ├── utils/                  # Utilities
│   │   ├── api_key_manager.py # macOS Keychain integration
│   │   └── helpers.py
│   └── analysis/               # Data quality analytics
├── tests/                      # Test suite
│   ├── test_api_key_manager.py
│   └── test_phase2_integration.py
├── utilities/                  # CLI tools
│   ├── smart_refresh.py        # Main data refresh tool
│   ├── batch_monitor.py        # Background batch processor
│   ├── sync_sp500.py           # S&P 500 composition sync
│   └── backup_database.py
├── docs/                       # Documentation
├── data/
│   └── stock_data.db          # SQLite database
├── analytics_dashboard.py      # PRIMARY dashboard
├── launcher_macos.py           # macOS launcher
├── StockAnalyzer.spec          # PyInstaller config
└── streamlit_app.py           # LEGACY dashboard (to be archived)
```

---

## 🧠 Development Guidelines

### **Core Principles**

1. **User Confirmation First**
   - When in doubt, ask user before proceeding
   - Never deviate from agreed upon plan without confirming
   - No assumptions without explicit approval

2. **Rigorous Testing**
   - Test functionality at every step
   - Verify todos are complete before marking as complete
   - Test both success and failure scenarios

3. **Clean Development**
   - Remove temporary files created during development
   - Keep codebase maintainable
   - No debugging artifacts left behind

4. **Documentation & Version Control**
   - Update README and CLAUDE.md upon phase completion
   - Create comprehensive commit messages
   - Commit and push after each completed phase

5. **Systematic Approach**
   - Use TodoWrite tool to track progress
   - Follow agreed upon plans step by step
   - Communicate status and blockers clearly

6. **Professional Communication**
   - Avoid hyperbole ("revolutionary", "breakthrough")
   - Use factual, measured language
   - Focus on technical accuracy

### **Quality Assurance Checklist**
Before marking any major feature complete:
- [ ] All functionality tested and working
- [ ] Error handling and edge cases covered
- [ ] Documentation updated (README.md, CLAUDE.md)
- [ ] No temporary files in repository
- [ ] Git commit created with descriptive message
- [ ] Changes pushed to remote
- [ ] User confirmation for any deviations

---

## 🎯 Current Priorities

### **✅ Production Distribution Ready**
**Status:** Phase 2-5 COMPLETE (macOS version)
**Key Achievements:**
- ✅ API Key Security Migration complete (macOS Keychain)
- ✅ macOS application bundling working (PyInstaller)
- ✅ CI/CD pipeline operational (GitHub Actions)
- ✅ Complete documentation suite
- ✅ All 38 tests passing

**What's Available:**
- Automated builds via CI/CD
- Manual builds via PyInstaller
- DMG installer creation
- First-launch wizard for API setup
- Secure credential storage (macOS Keychain)
- Complete user and developer documentation

**To Create Release:**
- Option A: Use CI/CD (GitHub Actions → Promote to Prod)
- Option B: Manual build (see `docs/BUILD_AND_DISTRIBUTE.md`)
- Option C: Follow checklist (see `docs/DEPLOYMENT_CHECKLIST.md`)

### **Future Enhancements (Not Prioritized)**
- Dashboard consolidation (merge `streamlit_app.py`)
- Portfolio tracking features
- Alerts and notifications
- Export to Excel/CSV
- Windows/Linux support

---

## 🔧 Quick Reference Commands

### **Data Collection**
```bash
# Full S&P 500 refresh
python utilities/smart_refresh.py --data-types all --force

# Specific stocks
python utilities/smart_refresh.py --symbols AAPL MSFT --data-types fundamentals

# Check S&P 500 composition changes
python utilities/smart_refresh.py --check-sp500

# Sync S&P 500 (add new, mark removed as inactive)
python utilities/smart_refresh.py --sync-sp500
```

### **Sentiment Processing**
```bash
# Submit batch for processing
python utilities/smart_refresh.py --process-sentiment

# Submit and wait for completion
python utilities/smart_refresh.py --process-sentiment --poll

# Finalize specific batch
python utilities/smart_refresh.py --finalize-batch <batch_id>

# Background monitor (auto-processes batches)
python utilities/batch_monitor.py
```

### **Dashboard**
```bash
# Primary dashboard (analytics_dashboard.py)
streamlit run analytics_dashboard.py

# Legacy dashboard (streamlit_app.py) - to be archived
streamlit run streamlit_app.py
```

### **Database Operations**
```bash
# Backup database
python utilities/backup_database.py

# Check sentiment status
sqlite3 data/stock_data.db "SELECT COUNT(*) FROM news_articles WHERE sentiment_score IS NULL"
sqlite3 data/stock_data.db "SELECT COUNT(*) FROM reddit_posts WHERE sentiment_score IS NULL"

# Check calculated metrics
sqlite3 data/stock_data.db "SELECT COUNT(*) FROM calculated_metrics WHERE composite_score IS NOT NULL"
```

---

## ⚠️ Important Configuration Notes

### **API Keys**
**Production (Bundled App):**
- Stored in macOS Keychain via APIKeyManager
- User-provided during first launch
- Service name: "StockAnalyzer-Pro"
- Fully secure, encrypted storage

**Development (.env file):**
```bash
# Reddit API (required for social sentiment)
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_secret
REDDIT_USER_AGENT=StockAnalyzer:v1.0

# Claude/Anthropic API (for sentiment analysis)
NEWS_API_KEY=sk-ant-api03-...  # Actually Anthropic, not news API
```

**Architecture:** APIKeyManager prioritizes Keychain → .env → graceful degradation

### **Quality Thresholds**
Location: `src/calculations/composite.py:93-99`
- Currently: 50%+ for components, 60% overall
- Restored from relaxed values after fixing refresh methods

### **Database Backups**
- Always backup before major changes: `python utilities/backup_database.py`
- Current backups in repo (can delete after verification):
  - `data/stock_data.db.backup_20251120_083207`
  - `data/stock_data.db.backup_20251120_083237`

---

## 📚 Reference Documentation

**Methodology:**
- `METHODS.md` - Detailed scoring algorithms and calculations

**For End Users:**
- `docs/USER_INSTALLATION_GUIDE.md` - Complete installation guide
- `README.md` - Quick start and overview

**For Developers:**
- `docs/GETTING_STARTED.md` - Developer setup and workflow
- `docs/BUILD_AND_DISTRIBUTE.md` - Building and distribution guide
- `docs/DEPLOYMENT_CHECKLIST.md` - Step-by-step deployment guide
- `docs/CICD_USAGE.md` - CI/CD pipeline usage guide
- `docs/CICD_QUICK_REFERENCE.md` - Quick reference card

**Implementation Plans:**
- `docs/IMPLEMENTATION_ROADMAP.md` - Production distribution plan (COMPLETE)
- `docs/API_KEY_MIGRATION.md` - API key security architecture (COMPLETE)

**Historical:**
- `docs/CHANGELOG.md` - Complete session history and bug fixes
- `docs/archive/` - Archived documentation from previous versions

**Testing:**
- `docs/TEST_PLAN.md` - Batch processing testing procedures
- `docs/BATCH_MONITOR_SETUP.md` - Background monitor setup

---

## 🚀 Quick Context for Common Tasks

### **Adding New Features**
1. Discuss approach with user first
2. Create TodoWrite list for tracking
3. Test incrementally
4. Update documentation
5. Commit with descriptive message

### **Fixing Bugs**
1. Understand root cause before fixing
2. Check for similar issues elsewhere
3. Add tests to prevent regression
4. Document fix in commit message
5. Update CHANGELOG.md if significant

### **Data Collection Issues**
- Check API credentials in `.env`
- Verify rate limits not exceeded (Reddit: 60/min)
- Check database schema matches code expectations
- Review `collectors.py` for recent changes

### **Sentiment Processing Issues**
- Check batch_mapping table for tracking
- Verify Anthropic API key is valid
- Check batch status via dashboard or CLI
- Review `unified_bulk_processor.py` for errors

### **Dashboard Issues**
- Check which dashboard is running (port 8501)
- Verify database has data to display
- Check Streamlit session state for stale data
- Review browser console for JavaScript errors

---

**Last System Verification:** November 20, 2025 (Late Session)
**Database State:** Fully operational, 100% sentiment coverage
**Production Status:** ✅ Ready for distribution (macOS)
**Phases Complete:** Phase 1-5 (Core functionality, Security, Build system, CI/CD)
