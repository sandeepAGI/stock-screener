# Deployment Checklist

**StockAnalyzer Pro - Complete Build and Distribution Guide**

This checklist provides step-by-step instructions for building and sharing the StockAnalyzer Pro application.

---

## 📋 Pre-Deployment Checklist

Before building or releasing:

- [ ] All tests passing: `python -m pytest tests/ -v`
- [ ] Security check passed (no API keys in code)
- [ ] CHANGELOG.md updated with recent changes
- [ ] Version number decided (e.g., v1.0.0)
- [ ] All changes committed and pushed to main

---

## 🚀 Option A: Automated Release (Recommended)

**Time:** ~15 minutes total (mostly automated)

### Step 1: Verify Tests Pass on Main

```bash
# Check GitHub Actions
# Go to: https://github.com/yourusername/stock-outlier/actions
# Ensure "Test on Main" workflow shows green checkmark ✅
```

### Step 2: Promote to Production

**Via GitHub UI:**
1. Go to **Actions** tab
2. Click **"Promote Main to Prod"** workflow
3. Click **"Run workflow"** button
4. Fill in:
   - **Version:** `v1.0.0` (or your version number)
   - **Create Release:** ✅ Check this box
5. Click **"Run workflow"**

**Via Command Line:**
```bash
gh workflow run promote-to-prod.yml \
  -f version=v1.0.0 \
  -f create_release=true
```

### Step 3: Wait for Automation

**What happens automatically:**
- ✅ Tests run on main branch
- ✅ Security checks verify no API keys
- ✅ Main branch merges to prod
- ✅ Version tag created
- ✅ macOS app builds
- ✅ Security checks on built app
- ✅ DMG installer created
- ✅ GitHub Release published

**Check progress:**
- Go to **Actions** tab
- Watch workflows complete (green checkmarks)

### Step 4: Download and Test

1. Go to **Releases** page: `https://github.com/yourusername/stock-outlier/releases`
2. Find your version (e.g., v1.0.0)
3. Download `StockAnalyzer-macOS-v1.0.0.dmg`
4. Test on your Mac:
   - Open the DMG
   - Drag app to Applications
   - Right-click → Open (first time)
   - Verify first-launch wizard appears
   - Test API key configuration

### Step 5: Share with Partner

**Send to Aileron Partner:**
```
Subject: StockAnalyzer Pro - Download Link

Hi [Partner Name],

StockAnalyzer Pro v1.0.0 is ready for download:

Download: https://github.com/yourusername/stock-outlier/releases/latest

Installation Instructions:
https://github.com/yourusername/stock-outlier/blob/main/docs/USER_INSTALLATION_GUIDE.md

Key Features:
- AI-Powered Sentiment Analysis (Claude)
- Multi-Factor Stock Scoring
- Social Media Tracking (Reddit)
- Interactive Dashboard

Requirements:
- macOS 10.13 or later
- Reddit API credentials (free)
- Claude API key (usage-based pricing)

Let me know if you have any questions!

Best,
[Your Name]
```

---

## 🔨 Option B: Manual Local Build

**Time:** 10-15 minutes

### Step 1: Verify Environment

```bash
# Ensure you're on latest main
git checkout main
git pull origin main

# Verify Python version
python --version  # Should be 3.12+

# Ensure dependencies installed
pip install -r requirements.txt
pip install pyinstaller
```

### Step 2: Run Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Expected: 38/38 tests passing
# If any fail, fix before proceeding
```

### Step 3: Security Check

```bash
# Check for API keys in code
grep -r "yeKIESP30pvI8o9ZU9JLBg" --exclude-dir=.git .
grep -r "sk-ant-api03-" --exclude-dir=.git --exclude="*.example" .

# Both should return no results
# If keys found, remove them before building
```

### Step 4: Build Application

```bash
# Clean previous builds
rm -rf build/ dist/

# Build with PyInstaller
pyinstaller StockAnalyzer.spec

# Expected output: dist/StockAnalyzer.app
# Build time: 5-10 minutes
```

### Step 5: Verify Build

```bash
# Check app was created
ls -lh dist/StockAnalyzer.app

# Verify no API keys in built app
cd dist/
grep -r "yeKIESP30pvI8o9ZU9JLBg" StockAnalyzer.app || echo "✓ No Reddit keys"
grep -r "sk-ant-api03" StockAnalyzer.app || echo "✓ No Claude keys"
cd ..

# Should see both ✓ messages
```

### Step 6: Test Application

```bash
# Test from terminal (see output)
./dist/StockAnalyzer.app/Contents/MacOS/StockAnalyzer

# Or open normally
open dist/StockAnalyzer.app

# Verify:
# - App launches
# - Dashboard appears in browser
# - First-launch wizard shown
# - Can configure API keys
# - Dashboard loads data
```

### Step 7: Create DMG Installer

```bash
# Create DMG for distribution
hdiutil create -volname "StockAnalyzer Pro" \
  -srcfolder dist/StockAnalyzer.app \
  -ov -format UDZO \
  StockAnalyzer-macOS-v1.0.0.dmg

# Verify DMG created
ls -lh StockAnalyzer-macOS-v1.0.0.dmg

# Expected size: 200-300 MB
```

### Step 8: Test DMG

```bash
# Mount DMG
open StockAnalyzer-macOS-v1.0.0.dmg

# Verify:
# - DMG opens
# - Shows StockAnalyzer.app
# - Can drag to Applications
# - Can launch from Applications folder
```

### Step 9: Share DMG

**Methods to share:**

1. **Email** (if <25MB after compression)
2. **File sharing services:**
   - Google Drive
   - Dropbox
   - WeTransfer
3. **GitHub Release** (manual):
   ```bash
   # Create release via GitHub UI
   # Upload StockAnalyzer-macOS-v1.0.0.dmg as asset
   ```

---

## 🔧 Troubleshooting

### Build Fails

**Problem:** PyInstaller errors during build

**Solutions:**
```bash
# Check PyInstaller version
pip show pyinstaller

# Reinstall if needed
pip uninstall pyinstaller
pip install pyinstaller

# Clean and rebuild
rm -rf build/ dist/
pyinstaller StockAnalyzer.spec --clean
```

### App Won't Launch

**Problem:** "App is damaged" or security warning

**Solutions:**
```bash
# Remove quarantine attribute
xattr -cr dist/StockAnalyzer.app

# Or sign the app (requires Apple Developer account)
codesign --deep --force --sign - dist/StockAnalyzer.app
```

### Missing Dependencies

**Problem:** Import errors when running app

**Solutions:**
```bash
# Check StockAnalyzer.spec hiddenimports
# Add any missing imports to hiddenimports list

# Rebuild after changes
pyinstaller StockAnalyzer.spec --clean
```

### Security Check Fails

**Problem:** API keys found in code or built app

**Solutions:**
```bash
# Find the key
grep -r "sk-ant-api03-" --exclude-dir=.git .

# Remove from code
# Ensure .env is in .gitignore
# Rebuild application
```

---

## 📊 Build Verification Checklist

Before distributing, verify:

- [ ] App launches successfully
- [ ] First-launch wizard appears
- [ ] Can configure Reddit API keys
- [ ] Can configure Claude API key
- [ ] Dashboard loads without errors
- [ ] Can collect data for test stock
- [ ] Sentiment analysis works
- [ ] No API keys bundled in app
- [ ] DMG installs correctly
- [ ] App works from Applications folder
- [ ] No Python required on target machine

---

## 📦 Distribution Checklist

Before sending to partner:

- [ ] Version number is correct
- [ ] DMG file created and tested
- [ ] Installation guide updated
- [ ] Release notes written
- [ ] Support contact provided
- [ ] API key setup instructions included
- [ ] Cost estimates are accurate
- [ ] Troubleshooting guide available

---

## 🎯 Quick Reference

### Build Commands

```bash
# Full build process
python -m pytest tests/ -v
pyinstaller StockAnalyzer.spec
./dist/StockAnalyzer.app/Contents/MacOS/StockAnalyzer
hdiutil create -volname "StockAnalyzer Pro" \
  -srcfolder dist/StockAnalyzer.app \
  -ov -format UDZO \
  StockAnalyzer-macOS-v1.0.0.dmg
```

### Security Verification

```bash
# Before build
grep -r "sk-ant-api03-" --exclude-dir=.git --exclude="*.example" .

# After build
cd dist/
grep -r "sk-ant-api03" StockAnalyzer.app || echo "✓ Clean"
```

### CI/CD Promotion

```bash
# Automated release
gh workflow run promote-to-prod.yml -f version=v1.0.0 -f create_release=true
```

---

## 📞 Support Resources

**Documentation:**
- [User Installation Guide](USER_INSTALLATION_GUIDE.md)
- [Build and Distribute Guide](BUILD_AND_DISTRIBUTE.md)
- [CI/CD Usage Guide](CICD_USAGE.md)
- [Getting Started Guide](GETTING_STARTED.md)

**GitHub:**
- Actions: `https://github.com/yourusername/stock-outlier/actions`
- Releases: `https://github.com/yourusername/stock-outlier/releases`

---

**Last Updated:** November 20, 2025
**Version:** 1.0.0
