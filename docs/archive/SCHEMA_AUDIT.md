# Complete Schema vs Code Audit

## Database Schemas (ACTUAL)

### batch_mapping
- ✅ id (PK)
- ✅ batch_id
- ✅ record_type
- ✅ record_id
- ✅ custom_id
- ✅ symbol
- ✅ status
- ✅ processed_at
- ✅ created_at

### news_articles
- ✅ id (PK)
- ✅ symbol
- ✅ title
- ✅ summary
- ✅ content
- ✅ publisher
- ✅ publish_date
- ✅ url
- ✅ sentiment_score
- ✅ data_quality_score
- ✅ created_at

### reddit_posts
- ✅ id (PK)
- ✅ symbol
- ✅ post_id
- ✅ title
- ✅ content
- ✅ subreddit
- ✅ author
- ✅ score
- ✅ upvote_ratio
- ✅ num_comments
- ✅ created_utc
- ✅ url
- ✅ sentiment_score
- ✅ data_quality_score
- ✅ created_at

## Code Audit Results

### ✅ CORRECT: unified_bulk_processor.py

**Line 257-259: INSERT INTO batch_mapping**
```sql
INSERT INTO batch_mapping
(batch_id, custom_id, record_type, record_id, symbol, status)
VALUES (?, ?, ?, ?, ?, 'submitted')
```
Status: ✅ All columns exist

**Line 358-363: UPDATE batch_mapping (after fix)**
```sql
UPDATE batch_mapping
SET status = 'completed', processed_at = CURRENT_TIMESTAMP
WHERE batch_id = ? AND custom_id = ?
```
Status: ✅ All columns exist

**Line 372-375: UPDATE news_articles**
```sql
UPDATE news_articles
SET sentiment_score = ?, data_quality_score = ?
WHERE id = ?
```
Status: ✅ All columns exist

**Line 380-383: UPDATE reddit_posts**
```sql
UPDATE reddit_posts
SET sentiment_score = ?, data_quality_score = ?
WHERE id = ?
```
Status: ✅ All columns exist

### ⚠️ LOGIC ISSUE: database.py

**Line 1352: get_unprocessed_items_for_batch (news)**
```sql
WHERE (n.sentiment_score IS NULL OR n.sentiment_score = 0.0)
```
Issue: Includes items with score=0.0 (neutral sentiment) as "unprocessed"
Impact: Re-processes already processed items with neutral sentiment
Severity: MEDIUM - causes unnecessary API calls but not data corruption

**Line 1377: get_unprocessed_items_for_batch (reddit)**
```sql
WHERE (r.sentiment_score IS NULL OR r.sentiment_score = 0.0)
```
Same issue as above

### ✅ CORRECT: dashboard (after fix)

**Line 1082-1092: Status detection**
```sql
SELECT COUNT(*) FROM news_articles WHERE sentiment_score IS NULL
SELECT COUNT(*) FROM reddit_posts WHERE sentiment_score IS NULL
```
Status: ✅ Fixed - only counts NULL

## Summary

### Fixed Issues:
1. ✅ batch_mapping.sentiment_score - REMOVED (column doesn't exist)
2. ✅ batch_mapping.confidence - REMOVED (column doesn't exist)
3. ✅ batch_mapping.error_message - REMOVED (column doesn't exist)
4. ✅ Dashboard status WHERE clause - FIXED (only NULL)

### Remaining Issues:
1. ⚠️ get_unprocessed_items_for_batch() includes score=0.0 items
   - Should change to: `WHERE n.sentiment_score IS NULL`
   - Affects: Batch submission, counts unprocessed items incorrectly

### All Column References Valid:
- ✅ batch_mapping: All references use existing columns
- ✅ news_articles: All references use existing columns
- ✅ reddit_posts: All references use existing columns
- ✅ No typos or missing columns in UPDATE/INSERT statements
