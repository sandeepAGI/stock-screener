# StockAnalyzer Pro - User Acceptance Testing (UAT) Plan
**Version:** 0.2.0-optimized
**Date:** November 26, 2025
**Build:** StockAnalyzerPro-v0.2.0-optimized.dmg (296MB)

---

## Pre-UAT Setup

### Database Backup Status
✅ **Backup Created:** `data/stock_data.db.backup_pre_uat_20251126_142231` (82MB)

**To Restore (if needed):**
```bash
cd /Users/sandeepmangaraj/myworkspace/Utilities/stock-outlier
cp data/stock_data.db.backup_pre_uat_20251126_142231 data/stock_data.db
```

### Expected Behavior
- **Development mode** uses: `/Users/sandeepmangaraj/myworkspace/Utilities/stock-outlier/data/stock_data.db`
- **Frozen app** uses: `~/Library/Application Support/StockAnalyzer/stock_data.db`
- These are completely isolated - no cross-contamination

---

## Phase 1: Database Isolation Verification

### Test 1.1: Check Development Database Remains Untouched
**Purpose:** Verify dev database is not accessed by frozen app

**Steps:**
1. Note current dev database modification time:
   ```bash
   ls -l data/stock_data.db
   ```
   Expected: `Nov 24 16:45` (or your current timestamp)

2. Keep this terminal open to verify after app launch

**Pass Criteria:** Timestamp does NOT change after launching frozen app

---

### Test 1.2: Verify Frozen App Uses Application Support
**Purpose:** Confirm frozen app creates isolated database

**Steps:**
1. Check if Application Support database exists:
   ```bash
   ls -lh ~/Library/Application\ Support/StockAnalyzer/
   ```

2. If database exists, note its size and timestamp

3. If it doesn't exist, that's fine - it will be created on first launch

**Pass Criteria:** Either database exists OR directory will be created on launch

---

## Phase 2: Application Launch

### Test 2.1: Mount DMG and Launch App
**Purpose:** Verify DMG mounts and app launches successfully

**Steps:**
1. Double-click `StockAnalyzerPro-v0.2.0-optimized.dmg`
2. Wait for DMG to mount (should open Finder window)
3. Drag `StockAnalyzer.app` to Applications folder
4. Eject the DMG
5. Navigate to Applications folder
6. Double-click `StockAnalyzer.app`

**Expected Behavior:**
- App launches (may see bouncing icon in dock)
- After 3 seconds, browser opens automatically to `http://localhost:8501`
- Dashboard loads in browser

**Pass Criteria:**
- ✅ App launches without errors
- ✅ Browser opens automatically
- ✅ Dashboard loads within 10 seconds

**Failure Indicators:**
- ❌ App crashes immediately
- ❌ Browser doesn't open after 30 seconds
- ❌ Error messages in browser

---

### Test 2.2: Verify Console for Errors
**Purpose:** Check for any runtime errors

**Steps:**
1. While app is running, open Terminal
2. Run:
   ```bash
   log stream --predicate 'processImagePath contains "StockAnalyzer"' --level debug
   ```
3. Watch for any ERROR or CRITICAL messages

**Pass Criteria:** No ERROR or CRITICAL messages related to database, imports, or core functionality

---

## Phase 3: Database Functionality

### Test 3.1: Verify Database Location
**Purpose:** Confirm frozen app is using correct database location

**Steps:**
1. In the dashboard, go to "Individual Stock Analysis" tab
2. Enter a stock symbol that you KNOW exists in your dev database (e.g., "AAPL")
3. Check if data appears

**Expected Behavior:**
- If Application Support database is NEW: "No data found" (correct - empty database)
- If Application Support database EXISTS: Data appears from that database

4. Now check what's in the Application Support database:
   ```bash
   sqlite3 ~/Library/Application\ Support/StockAnalyzer/stock_data.db "SELECT COUNT(*) FROM stocks"
   ```

**Pass Criteria:**
- ✅ App uses Application Support database (not dev database)
- ✅ Database schema is created correctly
- ✅ No crashes when accessing database

---

### Test 3.2: Verify Dev Database Untouched
**Purpose:** Final confirmation dev database is safe

**Steps:**
1. Check dev database timestamp again:
   ```bash
   ls -l data/stock_data.db
   ```

2. Compare with timestamp from Test 1.1

**Pass Criteria:** Timestamp is IDENTICAL (dev database was never accessed)

---

## Phase 4: Core Functionality Testing

### Test 4.1: Dashboard UI Load
**Purpose:** Verify all dashboard tabs load correctly

**Steps:**
1. Click through each tab in the sidebar:
   - 📊 Top Ranked Stocks
   - 🔍 Individual Stock Analysis
   - 📈 Trending Stocks
   - 🎯 Bulk Analysis
   - 🧮 Score Distribution
   - ⚙️ Settings

2. For each tab, verify:
   - Tab switches without error
   - UI elements render correctly
   - No JavaScript console errors (F12 -> Console)

**Pass Criteria:**
- ✅ All tabs load
- ✅ No console errors
- ✅ UI is responsive

---

### Test 4.2: Plotly Charts Render
**Purpose:** Verify plotly visualization library works

**Steps:**
1. Go to "📊 Top Ranked Stocks" tab
2. If data exists, verify charts render
3. If no data, that's expected (empty database)

4. Try hovering over any chart (if data exists)
5. Try zooming/panning (if data exists)

**Pass Criteria:**
- ✅ Charts render without errors (if data exists)
- ✅ Interactive features work (if data exists)
- ✅ If no data, shows "No data available" message (not crash)

---

### Test 4.3: Settings Tab
**Purpose:** Verify configuration UI works

**Steps:**
1. Go to "⚙️ Settings" tab
2. Verify all settings display
3. Try toggling a setting (if editable)
4. Check for any errors

**Pass Criteria:**
- ✅ Settings tab loads
- ✅ No errors in UI
- ✅ Configuration displays correctly

---

### Test 4.4: Individual Stock Analysis (Critical Feature)
**Purpose:** Test stock lookup functionality

**Steps:**
1. Go to "🔍 Individual Stock Analysis" tab
2. Enter a stock symbol: "AAPL"
3. Click "Analyze" or press Enter

**Expected Behavior:**
- If database is empty: "No data found for AAPL"
- If database has data: Stock analysis displays

**Pass Criteria:**
- ✅ Search executes without errors
- ✅ Appropriate message displays
- ✅ No crashes or freezes

---

## Phase 5: Performance Verification

### Test 5.1: Application Size
**Purpose:** Verify size optimization

**Steps:**
1. Check application size:
   ```bash
   du -sh /Applications/StockAnalyzer.app
   ```

**Expected:** ~714MB (down from 2.9GB)

**Pass Criteria:** Application is 700-750MB

---

### Test 5.2: Launch Time
**Purpose:** Verify app launches reasonably fast

**Steps:**
1. Quit the app (Cmd+Q)
2. Time the relaunch:
   - Note start time
   - Double-click app
   - Note when dashboard fully loads

**Expected:** 5-15 seconds (depending on system)

**Pass Criteria:**
- ✅ Launches within 20 seconds
- ✅ No excessive delays
- ✅ Browser opens within 5 seconds of Streamlit start

---

### Test 5.3: Memory Usage
**Purpose:** Check memory footprint

**Steps:**
1. Open Activity Monitor (Cmd+Space -> "Activity Monitor")
2. Search for "StockAnalyzer"
3. Note memory usage

**Expected:** 200-500MB (depending on data loaded)

**Pass Criteria:** Memory usage is reasonable (< 1GB)

---

## Phase 6: Edge Cases and Error Handling

### Test 6.1: Invalid Stock Symbol
**Purpose:** Verify error handling

**Steps:**
1. Go to Individual Stock Analysis
2. Enter invalid symbol: "ZZZZZZ"
3. Click Analyze

**Expected:** Error message "No data found" or similar

**Pass Criteria:**
- ✅ Graceful error message (not crash)
- ✅ App remains functional

---

### Test 6.2: Rapid Tab Switching
**Purpose:** Test UI stability

**Steps:**
1. Rapidly click through all tabs multiple times
2. Watch for errors or freezes

**Pass Criteria:**
- ✅ No crashes
- ✅ All tabs continue to work
- ✅ No memory leaks (check Activity Monitor)

---

### Test 6.3: App Quit and Restart
**Purpose:** Verify clean shutdown/restart

**Steps:**
1. Quit app (Cmd+Q)
2. Verify app closes (check Activity Monitor - should be gone)
3. Restart app
4. Verify dashboard loads again

**Pass Criteria:**
- ✅ Clean shutdown (no zombie processes)
- ✅ Clean restart
- ✅ Dashboard loads correctly

---

## Phase 7: Package Exclusions Verification

### Test 7.1: Verify Excluded Packages Not Present
**Purpose:** Confirm size optimization worked

**Steps:**
1. Check app bundle contents:
   ```bash
   ls -lh /Applications/StockAnalyzer.app/Contents/Frameworks/ | grep -i tensorflow
   ls -lh /Applications/StockAnalyzer.app/Contents/Frameworks/ | grep -i torch
   ls -lh /Applications/StockAnalyzer.app/Contents/Frameworks/ | grep -i opencv
   ```

**Expected:** No results (these packages should be excluded)

**Pass Criteria:** Excluded packages are not present

---

### Test 7.2: Verify Required Packages Present
**Purpose:** Confirm we didn't exclude necessary packages

**Steps:**
1. Check for required packages:
   ```bash
   ls -lh /Applications/StockAnalyzer.app/Contents/Frameworks/ | grep -i plotly
   ls -lh /Applications/StockAnalyzer.app/Contents/Frameworks/ | grep -i pandas
   ls -lh /Applications/StockAnalyzer.app/Contents/Frameworks/ | grep -i streamlit
   ```

**Expected:** These packages should be present

**Pass Criteria:** Required packages are included

---

## Phase 8: Production Readiness

### Test 8.1: Clean Machine Simulation
**Purpose:** Verify app works without Python installed

**Steps:**
1. In Terminal, temporarily rename your Python:
   ```bash
   # DON'T DO THIS - Just verify app doesn't need system Python
   # The app should be completely standalone
   ```

2. Launch app from Applications folder

**Expected:** App launches normally (doesn't depend on system Python)

**Pass Criteria:**
- ✅ App launches
- ✅ Dashboard works
- ✅ No Python import errors

---

### Test 8.2: Multi-Launch Test
**Purpose:** Verify app handles multiple launches gracefully

**Steps:**
1. With app already running, try to launch it again from Applications
2. Observe behavior

**Expected:** Either opens new browser tab OR shows error "port already in use"

**Pass Criteria:**
- ✅ Doesn't crash
- ✅ Original instance continues running
- ✅ Clear error message if can't start second instance

---

## Phase 9: Cleanup and Verification

### Test 9.1: Remove Test Installation
**Purpose:** Clean up test artifacts

**Steps:**
1. Quit the app
2. Remove from Applications:
   ```bash
   rm -rf /Applications/StockAnalyzer.app
   ```

3. Remove Application Support database (if you want clean slate):
   ```bash
   rm -rf ~/Library/Application\ Support/StockAnalyzer
   ```

**Note:** Only remove Application Support if you want to test fresh install again

---

### Test 9.2: Verify Dev Environment Intact
**Purpose:** Final confirmation dev environment is safe

**Steps:**
1. Check dev database is untouched:
   ```bash
   ls -l data/stock_data.db
   diff data/stock_data.db data/stock_data.db.backup_pre_uat_20251126_142231
   ```

2. Launch dev dashboard:
   ```bash
   streamlit run analytics_dashboard.py
   ```

3. Verify all your data is intact

**Pass Criteria:**
- ✅ Dev database unchanged
- ✅ Dev dashboard works normally
- ✅ All data present

---

## UAT Summary Checklist

**Critical Tests (Must Pass):**
- [ ] Database isolation (dev database untouched)
- [ ] App launches successfully
- [ ] Browser opens automatically
- [ ] Dashboard loads without errors
- [ ] No critical errors in logs
- [ ] App size is ~714MB (not 2.9GB)
- [ ] All tabs load correctly
- [ ] Clean shutdown and restart
- [ ] Dev environment remains functional

**Important Tests (Should Pass):**
- [ ] Plotly charts render (if data exists)
- [ ] Individual stock analysis works
- [ ] Settings tab loads
- [ ] Error handling works gracefully
- [ ] Memory usage reasonable
- [ ] Launch time < 20 seconds
- [ ] Excluded packages not present
- [ ] Required packages present

**Nice to Have (Can Fail):**
- [ ] Multi-launch handling
- [ ] Rapid tab switching
- [ ] Specific performance benchmarks

---

## Rollback Procedure (If UAT Fails)

If critical tests fail:

1. **Restore database:**
   ```bash
   cp data/stock_data.db.backup_pre_uat_20251126_142231 data/stock_data.db
   ```

2. **Remove failed installation:**
   ```bash
   rm -rf /Applications/StockAnalyzer.app
   rm -rf ~/Library/Application\ Support/StockAnalyzer
   ```

3. **Verify dev environment:**
   ```bash
   streamlit run analytics_dashboard.py
   ```

4. **Report issues:**
   - Which test(s) failed
   - Error messages observed
   - Screenshots if applicable
   - Console logs if available

---

## Success Criteria

**UAT PASSES if:**
- ✅ All Critical Tests pass
- ✅ At least 80% of Important Tests pass
- ✅ No data loss in development database
- ✅ App is functional and stable
- ✅ Size reduction achieved (75%)

**UAT FAILS if:**
- ❌ Any Critical Test fails
- ❌ Dev database corrupted or modified
- ❌ App crashes repeatedly
- ❌ Core functionality broken

---

## Post-UAT Actions

**If UAT Passes:**
1. Keep optimized DMG for distribution
2. Archive previous DMG files
3. Update documentation with UAT results
4. Prepare for distribution

**If UAT Fails:**
1. Execute rollback procedure
2. Document failures
3. Fix issues
4. Rebuild and re-test

---

**Tester:** Sandeep Mangaraj
**Date:** _______________
**Result:** ☐ PASS | ☐ FAIL
**Notes:** _______________
