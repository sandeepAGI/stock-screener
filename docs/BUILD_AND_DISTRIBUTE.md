# StockAnalyzer Pro - Build and Distribution Guide

**For Developers:** How to build and distribute the macOS application

---

## 🏗️ Building the Application

### Prerequisites:
```bash
# Ensure all dependencies are installed
pip install -r requirements.txt
pip install pyinstaller

# Verify Phase 2 is complete
python -m pytest tests/test_phase2_integration.py -v
```

### Build Steps:

#### 1. Clean Previous Builds
```bash
# Remove old build artifacts
rm -rf build/ dist/ *.spec
```

#### 2. Build with PyInstaller
```bash
# Build the macOS application
pyinstaller StockAnalyzer.spec

# This will create:
# - dist/StockAnalyzer.app (macOS application bundle)
# - build/ (temporary build files - can be deleted)
```

#### 3. Verify the Build
```bash
# Check that the app was created
ls -lh dist/StockAnalyzer.app

# Verify no API keys bundled
grep -r "yeKIESP30pvI8o9ZU9JLBg" dist/StockAnalyzer.app || echo "✓ No Reddit keys found"
grep -r "sk-ant-api03" dist/StockAnalyzer.app || echo "✓ No Claude keys found"
grep -r "7yn6BwQiGJTRQrNUKXCYQJUISiu_dg" dist/StockAnalyzer.app || echo "✓ No secrets found"
```

#### 4. Test the Application
```bash
# Run the built application
open dist/StockAnalyzer.app

# Or from command line to see output:
./dist/StockAnalyzer.app/Contents/MacOS/StockAnalyzer
```

---

## 🧪 Testing Checklist

### Pre-Distribution Testing:

- [ ] **Security Verification**
  - [ ] No API keys found in bundle
  - [ ] No .env file bundled
  - [ ] API Key Manager initializes correctly

- [ ] **First Launch**
  - [ ] App opens without Python installed
  - [ ] First-launch wizard appears
  - [ ] Can enter and save API credentials

- [ ] **API Configuration**
  - [ ] Reddit credentials save to Keychain
  - [ ] Claude credentials save to Keychain
  - [ ] Test connection buttons work
  - [ ] Invalid credentials show proper errors

- [ ] **Data Collection**
  - [ ] Can collect Yahoo Finance data
  - [ ] Reddit collection works with user keys
  - [ ] Sentiment analysis works with user keys

- [ ] **Dashboard Functionality**
  - [ ] All tabs load correctly
  - [ ] Charts and graphs render
  - [ ] Individual stock analysis works
  - [ ] Settings can be modified

- [ ] **Performance**
  - [ ] App starts in < 10 seconds
  - [ ] Dashboard loads in < 5 seconds
  - [ ] No memory leaks during extended use

---

## 📦 Creating Distribution Package

### Option 1: DMG Installer (Recommended)

```bash
# Create a DMG installer
hdiutil create -volname "StockAnalyzer Pro" \
  -srcfolder dist/StockAnalyzer.app \
  -ov -format UDZO \
  StockAnalyzer-macOS-v1.0.0.dmg
```

### Option 2: Zip Archive

```bash
# Create a zip file
cd dist
zip -r ../StockAnalyzer-macOS-v1.0.0.zip StockAnalyzer.app
cd ..
```

---

## 🚀 Distribution Methods

### Method 1: GitHub Releases (Recommended)

1. **Create a Release:**
   ```bash
   git checkout prod
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

2. **Upload to GitHub:**
   - Go to GitHub → Releases → Draft a new release
   - Tag: `v1.0.0`
   - Title: `StockAnalyzer Pro v1.0.0 - macOS`
   - Upload: `StockAnalyzer-macOS-v1.0.0.dmg`
   - Include: `docs/USER_INSTALLATION_GUIDE.md` in description

3. **Release Notes Template:**
   ```markdown
   ## StockAnalyzer Pro v1.0.0

   ### 🎉 First Release

   #### Features:
   - Multi-factor stock analysis (Fundamental, Quality, Growth, Sentiment)
   - AI-powered sentiment analysis using Claude
   - Social media sentiment from Reddit
   - Secure API key storage in macOS Keychain
   - Interactive dashboard with real-time rankings

   #### Requirements:
   - macOS 10.13 or later
   - Reddit API credentials (free)
   - Claude API key (paid, ~$100 for initial S&P 500 analysis)

   #### Installation:
   1. Download `StockAnalyzer-macOS-v1.0.0.dmg`
   2. Open the DMG
   3. Drag StockAnalyzer.app to Applications
   4. Right-click and select "Open" for first launch
   5. Follow the setup wizard

   See [User Installation Guide](docs/USER_INSTALLATION_GUIDE.md) for details.
   ```

### Method 2: Direct Download

Host the DMG/ZIP on a file sharing service and share the link.

---

## 🔐 Security Best Practices

### Before Building:

1. **Verify .env is not included:**
   ```bash
   # Check .gitignore
   cat .gitignore | grep ".env"

   # Verify .env is ignored
   git check-ignore .env
   ```

2. **Verify PyInstaller spec excludes sensitive files:**
   ```python
   # In StockAnalyzer.spec:
   # This line should exist:
   a.datas = [entry for entry in a.datas if not entry[0].endswith('.env')]
   ```

3. **Test with clean keychain:**
   ```bash
   # Remove test keys from keychain
   security delete-generic-password -s "StockAnalyzer-Pro" 2>/dev/null || true

   # Build and verify wizard appears
   ```

### After Building:

1. **Search for API keys:**
   ```bash
   # Should return no matches
   grep -r "sk-ant-" dist/StockAnalyzer.app
   grep -r "REDDIT_CLIENT" dist/StockAnalyzer.app
   ```

2. **Check bundle contents:**
   ```bash
   # List all included files
   find dist/StockAnalyzer.app -type f | head -50

   # Look for any .env files
   find dist/StockAnalyzer.app -name ".env*"
   ```

---

## 🐛 Common Build Issues

### Issue: "Module not found" errors

**Solution:**
Add missing module to `hiddenimports` in `StockAnalyzer.spec`:
```python
hiddenimports=[
    'missing_module_name',
    ...
]
```

### Issue: Streamlit files not bundled

**Solution:**
Ensure data files are collected:
```python
streamlit_datas = collect_data_files('streamlit')
```

### Issue: App crashes on startup

**Solution:**
Build with console mode to see errors:
```python
# In StockAnalyzer.spec:
console=True,  # Change to True for debugging
```

### Issue: Database not found

**Solution:**
Launcher creates database in `~/.stockanalyzer/data/` for bundled apps.
Check that `STOCKANALYZER_DATA_DIR` environment variable is set in launcher.

---

## 📝 Release Checklist

Before distributing to users:

- [ ] All Phase 2 integration tests pass (38/38)
- [ ] No API keys in built bundle (verified with grep)
- [ ] First-launch wizard tested on clean install
- [ ] API credentials save/load from Keychain works
- [ ] Data collection works with user-provided keys
- [ ] Sentiment analysis works with user-provided keys
- [ ] App tested on clean macOS (no Python installed)
- [ ] Documentation is up-to-date
  - [ ] USER_INSTALLATION_GUIDE.md
  - [ ] README.md
  - [ ] CLAUDE.md
- [ ] Version numbers updated
  - [ ] StockAnalyzer.spec (CFBundleVersion)
  - [ ] Documentation files
- [ ] Git tag created and pushed
- [ ] GitHub Release created with DMG attached

---

## 🔄 Version Management

### Semantic Versioning:
- **Major (1.x.x):** Breaking changes, new major features
- **Minor (x.1.x):** New features, backward compatible
- **Patch (x.x.1):** Bug fixes, minor improvements

### Update Checklist:
1. Update version in `StockAnalyzer.spec`
2. Update version in documentation
3. Create changelog entry in `docs/CHANGELOG.md`
4. Commit changes to `main`
5. Merge to `prod`
6. Tag release: `git tag -a vX.Y.Z`
7. Build and distribute

---

## 📊 Build Statistics

**Expected Build Time:** 5-10 minutes
**Expected Bundle Size:** 200-300 MB
**Dependencies Bundled:** ~150 packages

---

## 🆘 Getting Help

If you encounter build issues:

1. Check this guide for common issues
2. Review PyInstaller logs in `build/StockAnalyzer/`
3. Search PyInstaller documentation
4. Create an issue with:
   - Error message
   - Build logs
   - Steps to reproduce

---

**Last Updated:** November 20, 2025
**For:** StockAnalyzer Pro v1.0.0
**Platform:** macOS
