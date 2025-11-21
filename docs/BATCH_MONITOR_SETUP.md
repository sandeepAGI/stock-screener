# Batch Monitor Setup Guide

## Overview

The **Batch Monitor** is a background service that automatically:
- ✅ Polls active batches every 5 minutes (configurable)
- ✅ Checks batch status in Anthropic API
- ✅ Automatically retrieves and processes results when complete
- ✅ Updates database with sentiment scores
- ✅ Logs all activity for debugging

**No more manual result processing!** Set it up once and forget about it.

---

## Quick Start

### Option 1: Run Manually (Testing)

```bash
# Run in foreground (see output)
python utilities/batch_monitor.py

# Run once and exit (no continuous polling)
python utilities/batch_monitor.py --once

# Run with custom interval (10 minutes = 600 seconds)
python utilities/batch_monitor.py --interval 600
```

### Option 2: Run in Background (Mac/Linux)

```bash
# Run in background with nohup
nohup python utilities/batch_monitor.py > /dev/null 2>&1 &

# Check if running
ps aux | grep batch_monitor

# Stop background process
pkill -f batch_monitor.py
```

### Option 3: Run as System Service (Recommended)

**Mac (launchd):**
```bash
# Install service
cp utilities/com.stockanalyzer.batchmonitor.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.stockanalyzer.batchmonitor.plist

# Start service
launchctl start com.stockanalyzer.batchmonitor

# Check status
launchctl list | grep batchmonitor

# View logs
tail -f logs/batch_monitor.log

# Stop service
launchctl stop com.stockanalyzer.batchmonitor

# Uninstall service
launchctl unload ~/Library/LaunchAgents/com.stockanalyzer.batchmonitor.plist
rm ~/Library/LaunchAgents/com.stockanalyzer.batchmonitor.plist
```

**Linux (systemd):**
```bash
# Create service file
sudo nano /etc/systemd/system/stockanalyzer-batch.service

# Paste this content (adjust paths):
[Unit]
Description=StockAnalyzer Batch Monitor
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/path/to/stock-outlier
ExecStart=/path/to/stock-outlier/venv/bin/python utilities/batch_monitor.py
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable stockanalyzer-batch
sudo systemctl start stockanalyzer-batch

# Check status
sudo systemctl status stockanalyzer-batch

# View logs
journalctl -u stockanalyzer-batch -f
```

---

## How It Works

### Workflow

```
1. Poll Cycle Starts (every 5 minutes)
   ↓
2. Get Active Batches from database
   ↓
3. For Each Batch:
   - Check status via Anthropic API
   - If status = "ended":
     → Retrieve all results
     → Update news_articles table
     → Update reddit_posts table
     → Mark batch as complete in batch_mapping
   - If status = "in_progress":
     → Log progress, wait for next cycle
   ↓
4. Sleep 5 minutes
   ↓
5. Repeat
```

### Database Flow

```
Batch Submitted → batch_mapping (status='submitted')
                          ↓
Background Monitor Checks Status
                          ↓
Anthropic Returns "ended"
                          ↓
Monitor Retrieves Results
                          ↓
batch_mapping (status='completed')
news_articles (sentiment_score updated)
reddit_posts (sentiment_score updated)
                          ↓
Dashboard Shows "✅ STEP 2: COMPLETE"
```

---

## Configuration

### Poll Interval

Default: 300 seconds (5 minutes)

Change with `--interval` flag:
```bash
# Check every 2 minutes
python utilities/batch_monitor.py --interval 120

# Check every 10 minutes (less API calls)
python utilities/batch_monitor.py --interval 600
```

**Recommendation:** 5 minutes is optimal balance between responsiveness and API usage.

### Environment Variables

Required:
- `ANTHROPIC_API_KEY` or `NEWS_API_KEY` - Your Anthropic API key

Optional:
- Set in `.env` file or export in shell

### Logging

Logs are written to:
- **Main log:** `logs/batch_monitor.log`
- **Stdout:** `logs/batch_monitor_stdout.log` (service mode)
- **Stderr:** `logs/batch_monitor_stderr.log` (service mode)

Logs include:
- ✅ Successful processing
- ⏳ Progress updates
- ❌ Errors with stack traces
- 📊 Statistics (items processed, success/fail counts)

---

## Dashboard Integration

### Step 2 Status Indicators

**Before Completion:**
```
⏳ STEP 2: IN PROGRESS
📊 Status: 45,952 processed, 5,650 remaining
```

**After Completion (Automatic):**
```
✅ STEP 2: COMPLETE
🎉 All sentiment processing finished! All 51,602 items have been analyzed.
➡️ Ready for Step 3: Proceed to calculate final rankings below

📰 News Processed: 42,697
💭 Reddit Processed: 3,255
✅ Total Complete: 45,952
```

**No manual intervention needed!** The monitor updates the database, dashboard refreshes automatically show completion.

---

## Monitoring & Debugging

### Check Monitor Status

```bash
# Is it running?
ps aux | grep batch_monitor

# Recent activity (last 50 lines)
tail -50 logs/batch_monitor.log

# Watch live
tail -f logs/batch_monitor.log

# Filter for errors
grep ERROR logs/batch_monitor.log

# Filter for successes
grep "✅ Processed batch" logs/batch_monitor.log
```

### Manual Processing (If Needed)

If monitor fails or you need immediate processing:

```bash
# Process specific batch manually
python test_batch_processing.py <batch_id>

# Or use dashboard manual recovery
# Step 2 → Manual Batch Recovery → Enter batch ID
```

### Troubleshooting

**Problem: Monitor not starting**
```bash
# Check API key
echo $ANTHROPIC_API_KEY

# Check Python environment
which python
python --version

# Check dependencies
pip list | grep anthropic
```

**Problem: Monitor runs but doesn't process**
```bash
# Check for active batches
sqlite3 data/stock_data.db "SELECT * FROM batch_mapping WHERE status='submitted'"

# Check API connectivity
curl https://api.anthropic.com/v1/messages/batches

# Check logs for errors
grep -A 5 ERROR logs/batch_monitor.log
```

**Problem: Service won't start (Mac)**
```bash
# Check service file
cat ~/Library/LaunchAgents/com.stockanalyzer.batchmonitor.plist

# Check for errors
launchctl error
launchctl list | grep batch

# Check logs
cat logs/batch_monitor_stderr.log
```

---

## Cost & Performance

### API Usage

- **Poll check:** ~1 API call per batch per 5 minutes
- **Result retrieval:** 1 API call per batch (when complete)

For 1 batch running for 1 hour:
- Checks: 12 calls (1 per 5 min × 12 intervals)
- Retrieval: 1 call
- **Total:** 13 API calls

Cost is negligible compared to batch processing itself.

### System Resources

- **CPU:** ~0.1% when idle, ~2% when processing
- **Memory:** ~50MB
- **Network:** Minimal (status checks ~1KB, results vary by size)

Safe to run continuously on any modern system.

---

## Best Practices

### Recommendations

1. **Run as Service:** Set up launchd/systemd for auto-start after reboot
2. **Monitor Logs:** Check occasionally to ensure smooth operation
3. **Keep It Running:** Don't stop unless necessary (maintenance, updates)
4. **Alert on Errors:** Set up log monitoring if running in production

### Production Setup

```bash
# 1. Install as service
cp utilities/com.stockanalyzer.batchmonitor.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.stockanalyzer.batchmonitor.plist

# 2. Verify it's running
launchctl list | grep batchmonitor

# 3. Set up log rotation (optional)
# Add to logrotate or use macOS log rotation

# 4. Test with a batch submission
# Dashboard → Step 2 → Submit Batch
# Wait 5 minutes, check logs
tail -f logs/batch_monitor.log
```

---

## Examples

### Example 1: Process Your Current Batches

```bash
# You have 2 completed batches in Anthropic
# Start monitor once to process them immediately
python utilities/batch_monitor.py --once

# Output:
# 🔍 Checking status for batch msgbatch_01ABC...
# 🎉 Batch msgbatch_01ABC completed! Processing results...
# ✅ Processed batch msgbatch_01ABC
#    📈 Successful: 5650
#    ❌ Failed: 0
#
# 🔍 Checking status for batch msgbatch_02DEF...
# 🎉 Batch msgbatch_02DEF completed! Processing results...
# ✅ Processed batch msgbatch_02DEF
#    📈 Successful: 5650
#    ❌ Failed: 0
```

### Example 2: Continuous Monitoring

```bash
# Start monitor in background
nohup python utilities/batch_monitor.py > /dev/null 2>&1 &

# Submit batches throughout the day
# Monitor automatically processes them when complete
# Check dashboard - Step 2 shows "✅ COMPLETE" automatically
```

---

## FAQ

**Q: Does it process batches immediately after submission?**
A: No, it checks every 5 minutes. Max wait is 5 minutes after Anthropic completes processing.

**Q: Can I run multiple monitors?**
A: Not recommended. They might process the same batch twice. Run one instance only.

**Q: What if I restart my computer?**
A: Use launchd/systemd service - it auto-starts on boot.

**Q: How do I know it's working?**
A: Check `logs/batch_monitor.log` - should show poll cycles every 5 minutes.

**Q: Does it interfere with the dashboard?**
A: No, they're separate processes. Monitor updates database, dashboard displays it.

**Q: What if a batch fails to process?**
A: Check logs for errors. Can manually process with `test_batch_processing.py`.

---

## Summary

**Setup Once:**
```bash
# Install as service
cp utilities/com.stockanalyzer.batchmonitor.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.stockanalyzer.batchmonitor.plist
```

**Use Forever:**
- Submit batches in dashboard
- Monitor processes them automatically
- Dashboard shows "✅ STEP 2: COMPLETE"
- Proceed to Step 3

**No more manual processing!** 🎉
