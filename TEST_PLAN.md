# Complete End-to-End Test Plan

## Current Status ✅

**Database State (Verified):**
- News articles: 5,030 need processing, 42,697 already processed
- Reddit posts: 620 need processing, 3,255 already processed
- Total unprocessed: 5,650 items
- Total processed: 45,952 items

**Dashboard State (Verified):**
- ✅ Step 2 shows correct counts
- ✅ Step 3 shows "incomplete" warning (correct - 5,650 items remaining)

**Code Fixes Applied:**
- ✅ Fixed batch_mapping column references (removed non-existent columns)
- ✅ Fixed WHERE clauses (NULL only, not 0.0)
- ✅ Complete schema audit performed
- ✅ All SQL statements verified

---

## Test Plan: Complete the Workflow

### Test 1: Submit Remaining Batch (Step 2)

**Action:**
1. Go to dashboard Step 2
2. Click "🚀 Submit Batch" button
3. Should see: "✅ Batch submitted successfully!"
4. Should see: "📊 Processing 5,650 items"
5. Should see: "🆔 Batch ID: msgbatch_..."

**Expected Results:**
- ✅ Batch submission succeeds
- ✅ Batch ID displayed
- ✅ batch_mapping table NOW has 5,650 entries (verify with query below)
- ✅ Step 2 shows "Active Batch Processing" section

**Verification Query:**
```bash
sqlite3 data/stock_data.db "SELECT COUNT(*) FROM batch_mapping"
# Should show: 5650
```

### Test 2: Monitor Batch Status (Step 2)

**Action:**
1. Wait ~1 hour (or check Anthropic console)
2. Refresh dashboard
3. Check "Batch Processing Status" section

**Expected Results:**
- ✅ Shows batch progress (X/5650 completed)
- ✅ Status changes from "in_progress" to "ended"
- ✅ "📥 Process Results" button appears when ended

### Test 3: Process Batch Results (Step 2)

**Action:**
1. Click "📥 Process Results" button
2. Wait for processing (should be quick ~1-2 minutes)

**Expected Results:**
- ✅ Shows "✅ Results processed successfully!"
- ✅ Shows "📊 Updated 5,650 items" (or close to it)
- ✅ Dashboard refreshes automatically

**Verification Query:**
```bash
sqlite3 data/stock_data.db "SELECT
  (SELECT COUNT(*) FROM news_articles WHERE sentiment_score IS NULL) as news_null,
  (SELECT COUNT(*) FROM reddit_posts WHERE sentiment_score IS NULL) as reddit_null,
  (SELECT COUNT(*) FROM batch_mapping WHERE status='completed') as completed"
```

Expected:
- news_null: ~0 (or very low)
- reddit_null: ~0 (or very low)
- completed: ~5650

### Test 4: Verify Step 3 Status Update

**Action:**
1. After processing results, scroll to Step 3
2. Check status message

**Expected Results:**
- ✅ Shows: "✅ **Ready for final calculations.** All sentiment data is up-to-date."
- ✅ NO warning about incomplete processing
- ✅ Calculate button should be available

### Test 5: Run Final Calculations (Step 3)

**Action:**
1. Click calculate/refresh metrics button in Step 3
2. Wait for completion

**Expected Results:**
- ✅ Calculations complete successfully
- ✅ Composite scores updated
- ✅ Can view rankings and analysis

---

## Quick Verification Commands

### Check Current State:
```bash
# Unprocessed counts
sqlite3 data/stock_data.db "SELECT
  (SELECT COUNT(*) FROM news_articles WHERE sentiment_score IS NULL) as news,
  (SELECT COUNT(*) FROM reddit_posts WHERE sentiment_score IS NULL) as reddit"

# Batch tracking
sqlite3 data/stock_data.db "SELECT COUNT(*), status FROM batch_mapping GROUP BY status"

# Recent sentiment scores (should see new timestamps)
sqlite3 data/stock_data.db "SELECT COUNT(*), DATE(created_at)
  FROM news_articles
  WHERE sentiment_score IS NOT NULL
  GROUP BY DATE(created_at)
  ORDER BY DATE(created_at) DESC
  LIMIT 5"
```

### Run Diagnostic Anytime:
```bash
python test_batch_processing.py <batch_id>
```

---

## Success Criteria

**All Tests Pass If:**
- ✅ Batch submission creates entries in batch_mapping table
- ✅ Processing updates sentiment scores in news_articles/reddit_posts
- ✅ Step 3 status changes from "incomplete" to "ready"
- ✅ Final calculations work with complete data
- ✅ No SQL errors in logs
- ✅ Database state matches dashboard display

---

## Rollback Plan (If Needed)

If anything goes wrong:
```bash
# Check recent commits
git log --oneline -5

# Rollback to before fixes
git reset --hard <commit_hash>

# Or create backup now
python utilities/backup_database.py
```

---

## Notes

- Processing 5,650 items should take ~30-60 minutes in Anthropic
- You can continue using the system while batch processes
- Refresh dashboard to see updated status
- If batch fails, use manual recovery with batch ID
