# PyInstaller Implementation Plan - Programmatic Approach
**Date:** November 24, 2025
**Status:** Ready to implement
**Estimated Time:** 4-6 hours total

---

## Context

After two failed attempts with subprocess launcher pattern (v0.1.0, v0.1.1), we've reverted to commit `7888d1f` where the Streamlit dashboard works locally. This document outlines the correct approach using Streamlit's programmatic API.

**Key Learnings:**
- Subprocess launchers don't work with PyInstaller frozen apps
- `sys.executable` in frozen apps points to the app itself, not Python
- Streamlit CAN be bundled successfully using programmatic approach
- See `docs/LESSONS_LEARNED_PYINSTALLER.md` for detailed analysis

---

## Three-Phase Plan

### Phase 1: Core Bundling (1-2 hours)
**Goal:** Working DMG that launches Streamlit, uses .env for keys (not secure yet)

### Phase 2: API Key Security (2-3 hours)
**Goal:** Production-ready DMG with macOS Keychain integration

### Phase 3: Distribution Polish (1 hour)
**Goal:** Professional DMG with icon, installer, documentation

---

## PHASE 1: Core Bundling Implementation

### Step 1.1: Modify analytics_dashboard.py

**Location:** Bottom of `analytics_dashboard.py` (after all code, before current `if __name__ == "__main__"`)

**Add this code:**
```python
if __name__ == "__main__":
    import sys

    # Check if running as PyInstaller bundle
    if getattr(sys, 'frozen', False):
        # Running as bundled app - use programmatic Streamlit
        from streamlit.web import cli as stcli
        import os

        # Set up arguments for Streamlit
        sys.argv = [
            "streamlit",
            "run",
            __file__,
            "--server.headless=true",
            "--server.port=8501",
            "--server.address=localhost",
            "--browser.serverAddress=localhost",
            "--browser.gatherUsageStats=false",
            "--server.enableXsrfProtection=true",
            "--server.enableCORS=false",
            "--global.developmentMode=false",
            "--client.showErrorDetails=false",
        ]

        # Run Streamlit
        sys.exit(stcli.main())
    else:
        # Running in development mode - Streamlit handles it normally
        # This allows: streamlit run analytics_dashboard.py
        pass
```

**What this does:**
- Detects if running as frozen PyInstaller app
- If frozen: Imports Streamlit's CLI and runs it programmatically
- If not frozen: Normal Streamlit execution (for development)

---

### Step 1.2: Create PyInstaller Spec File

**File:** `StockAnalyzer.spec` (create new)

```python
# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for StockAnalyzer Pro - Programmatic Streamlit Approach

This uses analytics_dashboard.py as direct entry point with programmatic
Streamlit execution (no subprocess launcher needed).
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect Streamlit data files
streamlit_datas = collect_data_files('streamlit')
plotly_datas = collect_data_files('plotly')
altair_datas = collect_data_files('altair')

a = Analysis(
    ['analytics_dashboard.py'],  # Direct entry point
    pathex=[],
    binaries=[],
    datas=[
        # Source code
        ('src', 'src'),

        # Include .env.example as template
        ('.env.example', '.'),

        # Logo if exists
        ('src/data/Logo-Element-Retina.png', 'src/data'),

        # Streamlit dependencies
        *streamlit_datas,
        *plotly_datas,
        *altair_datas,
    ],
    hiddenimports=[
        # Streamlit
        'streamlit',
        'streamlit.runtime',
        'streamlit.runtime.scriptrunner',
        'streamlit.web',
        'streamlit.web.cli',

        # Plotting
        'plotly',
        'plotly.graph_objs',
        'plotly.express',

        # Data processing
        'pandas',
        'numpy',

        # Database
        'sqlite3',

        # Our modules
        'src.data.database',
        'src.data.collectors',
        'src.data.sentiment_analyzer',
        'src.data.unified_bulk_processor',
        'src.calculations.composite',
        'src.calculations.fundamental',
        'src.calculations.quality',
        'src.calculations.growth',
        'src.calculations.sentiment',

        # Additional dependencies
        'altair',
        'validators',
        'watchdog',
        'tornado',
        'pyarrow',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude test files
        'pytest',
        'tests',

        # Exclude dev tools
        'IPython',
        'notebook',
        'jupyter',

        # Exclude unused modules
        'matplotlib',
        'scipy',

        # Exclude geospatial (not needed)
        'pyogrio',
        'geopandas',
        'fiona',
        'shapely',
        'gdal',
        'osgeo',
    ],
    noarchive=False,
    optimize=0,
)

# Filter out None entries
a.datas = [entry for entry in a.datas if entry is not None]

# Remove .env files if somehow included (keep .env.example)
a.datas = [entry for entry in a.datas if not entry[0].endswith('.env') or entry[0].endswith('.env.example')]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='StockAnalyzer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window for clean GUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='StockAnalyzer',
)

app = BUNDLE(
    coll,
    name='StockAnalyzer.app',
    icon=None,
    bundle_identifier='com.stockanalyzer.app',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True',
        'CFBundleName': 'StockAnalyzer Pro',
        'CFBundleDisplayName': 'StockAnalyzer Pro',
        'CFBundleVersion': '0.2.0',
        'CFBundleShortVersionString': '0.2.0',
        'NSHumanReadableCopyright': 'Copyright © 2025',
    },
)
```

---

### Step 1.3: Build the App

```bash
# Clean previous builds
rm -rf build/ dist/

# Build with PyInstaller
pyinstaller StockAnalyzer.spec

# Verify build
ls -lh dist/StockAnalyzer.app
```

**Expected output:**
- `dist/StockAnalyzer.app` created
- Size: ~2-3GB
- Contains all dependencies

---

### Step 1.4: Test the App

**Test 1: From Terminal**
```bash
./dist/StockAnalyzer.app/Contents/MacOS/StockAnalyzer
```
Expected: Streamlit launches, browser opens automatically

**Test 2: Double-Click**
```bash
open dist/StockAnalyzer.app
```
Expected: App launches, browser opens to dashboard

**Test 3: Database Access**
- Verify app can read from bundled database
- Check that data displays correctly

---

### Step 1.5: Create DMG

```bash
hdiutil create -volname "StockAnalyzer Pro" \
  -srcfolder dist/StockAnalyzer.app \
  -ov -format UDZO \
  StockAnalyzer-macOS-v0.2.0.dmg
```

---

## PHASE 2: API Key Security

### Step 2.1: Recover API Key Components from Backup

```bash
# Check backup branch exists
git branch | grep backup/launcher-attempt-2025-11-23

# Extract API key manager
git show backup/launcher-attempt-2025-11-23:src/utils/api_key_manager.py > src/utils/api_key_manager.py

# Extract first-launch wizard UI
git show backup/launcher-attempt-2025-11-23:src/ui/api_config_ui.py > src/ui/api_config_ui.py

# Extract tests (optional, for verification)
git show backup/launcher-attempt-2025-11-23:tests/test_api_key_manager.py > tests/test_api_key_manager.py

# Verify files were recovered
ls -lh src/utils/api_key_manager.py
ls -lh src/ui/api_config_ui.py
```

**Files recovered:**
- `src/utils/api_key_manager.py` - macOS Keychain integration
- `src/ui/api_config_ui.py` - First-launch wizard with validation
- `tests/test_api_key_manager.py` - Unit tests

---

### Step 2.2: Integrate First-Launch Wizard

**Location:** Top of `analytics_dashboard.py`, right after imports, before any other code

```python
# Add to imports at top
from src.utils.api_key_manager import APIKeyManager
from src.ui.api_config_ui import show_api_config_wizard

# Add right after st.set_page_config()
def check_api_keys():
    """Check if API keys are configured, show wizard if not"""
    key_manager = APIKeyManager()

    # Check if all required keys are present
    if not key_manager.has_all_keys():
        st.warning("⚠️ API Keys Required")
        st.info("Please configure your API keys to use StockAnalyzer Pro.")
        show_api_config_wizard()
        st.stop()  # Stop execution until keys are configured

    return key_manager

# Call it before main dashboard code
key_manager = check_api_keys()
```

---

### Step 2.3: Update Data Collectors

**Files to modify:**
- `src/data/collectors.py`
- `src/data/sentiment_analyzer.py`
- `src/data/unified_bulk_processor.py`

**Pattern to apply:**

**Before (current):**
```python
reddit_client_id = os.getenv('REDDIT_CLIENT_ID')
```

**After (with Keychain fallback):**
```python
from src.utils.api_key_manager import APIKeyManager

key_manager = APIKeyManager()
reddit_client_id = key_manager.get_reddit_client_id()
# Fallback to .env for development
if not reddit_client_id:
    reddit_client_id = os.getenv('REDDIT_CLIENT_ID')
```

**Apply this pattern to all API key reads:**
- REDDIT_CLIENT_ID
- REDDIT_CLIENT_SECRET
- REDDIT_USER_AGENT
- NEWS_API_KEY (actually Anthropic key)

---

### Step 2.4: Update PyInstaller Spec

**Add to hiddenimports section:**
```python
hiddenimports=[
    # ... existing imports ...

    # API Key Management (Phase 2)
    'src.utils.api_key_manager',
    'src.ui.api_config_ui',
    'keyring',
    'keyring.backends',
    'keyring.backends.macOS',
],
```

---

### Step 2.5: Rebuild and Test

```bash
# Rebuild with API key security
rm -rf build/ dist/
pyinstaller StockAnalyzer.spec

# Test first launch (no keys in Keychain)
# Should show wizard
./dist/StockAnalyzer.app/Contents/MacOS/StockAnalyzer

# Test with keys configured
# Should skip wizard and load dashboard
```

---

## PHASE 3: Distribution Polish

### Step 3.1: Create Professional DMG

**Install create-dmg tool:**
```bash
brew install create-dmg
```

**Create DMG with Applications shortcut:**
```bash
create-dmg \
  --volname "StockAnalyzer Pro" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 100 \
  --icon "StockAnalyzer.app" 175 120 \
  --hide-extension "StockAnalyzer.app" \
  --app-drop-link 425 120 \
  "StockAnalyzer-macOS-v0.2.0.dmg" \
  "dist/StockAnalyzer.app"
```

---

### Step 3.2: Add App Icon (Optional)

1. Create 1024x1024 PNG icon
2. Convert to .icns: `sips -s format icns icon.png --out icon.icns`
3. Update spec file: `icon='icon.icns'`
4. Rebuild

---

### Step 3.3: Create Installation Guide

**File:** `docs/USER_INSTALLATION_GUIDE_v0.2.md`

**Contents:**
```markdown
# StockAnalyzer Pro v0.2 - Installation Guide

## System Requirements
- macOS 10.13 or later
- No Python installation required

## Installation Steps

1. **Download**
   - Download `StockAnalyzer-macOS-v0.2.0.dmg`

2. **Install**
   - Double-click the DMG
   - Drag "StockAnalyzer Pro" to Applications folder

3. **First Launch**
   - Right-click → Open (macOS security)
   - Click "Open" in security dialog

4. **Configure API Keys** (First launch only)
   - App will show setup wizard
   - Get Reddit API keys: https://www.reddit.com/prefs/apps
   - Get Anthropic API key: https://console.anthropic.com/
   - Enter keys in wizard
   - Click "Save & Continue"

5. **Done!**
   - Dashboard loads in browser
   - Keys securely stored in macOS Keychain
```

---

## Testing Checklist

### Phase 1 Testing
- [ ] App builds without errors
- [ ] App launches from terminal
- [ ] App launches via double-click
- [ ] Streamlit server starts
- [ ] Browser opens automatically
- [ ] Dashboard loads and displays data
- [ ] No console errors
- [ ] Can navigate between tabs
- [ ] Individual Analysis search works

### Phase 2 Testing
- [ ] First launch shows API key wizard
- [ ] Can enter API keys in wizard
- [ ] Keys save to macOS Keychain
- [ ] Dashboard loads after saving keys
- [ ] Subsequent launches skip wizard
- [ ] Data collection works with user keys
- [ ] Sentiment analysis works with user keys
- [ ] Can update keys via Settings tab

### Phase 3 Testing
- [ ] DMG mounts correctly
- [ ] Can drag to Applications folder
- [ ] App launches from Applications
- [ ] Icon displays correctly (if added)
- [ ] Installation guide is clear

---

## Known Issues & Solutions

### Issue: App won't open (security warning)
**Solution:** Right-click → Open (first launch only)

### Issue: "Developer cannot be verified"
**Solution:** System Preferences → Security → "Open Anyway"

### Issue: Port 8501 already in use
**Solution:** Kill existing Streamlit: `lsof -ti:8501 | xargs kill -9`

### Issue: Database not found
**Solution:** Check that .env or Keychain has correct DATABASE_PATH

### Issue: Keyring not working
**Solution:** Grant Keychain Access permissions in System Preferences

---

## File Structure After Implementation

```
stock-outlier/
├── analytics_dashboard.py          # Modified with programmatic Streamlit
├── StockAnalyzer.spec              # NEW - PyInstaller configuration
├── src/
│   ├── utils/
│   │   └── api_key_manager.py      # Recovered from backup
│   └── ui/
│       └── api_config_ui.py        # Recovered from backup
├── docs/
│   ├── PYINSTALLER_IMPLEMENTATION_PLAN.md  # This file
│   ├── LESSONS_LEARNED_PYINSTALLER.md
│   └── USER_INSTALLATION_GUIDE_v0.2.md
├── dist/
│   └── StockAnalyzer.app           # Built app bundle
└── StockAnalyzer-macOS-v0.2.0.dmg  # Distribution DMG
```

---

## Commit Strategy

### After Phase 1:
```bash
git add analytics_dashboard.py StockAnalyzer.spec
git commit -m "feat: Implement PyInstaller bundling with programmatic Streamlit

- Modified analytics_dashboard.py to detect frozen mode
- Added programmatic Streamlit execution via stcli.main()
- Created StockAnalyzer.spec for PyInstaller configuration
- Direct entry point (no subprocess launcher needed)
- Tested: App launches and runs Streamlit successfully

Working DMG created but uses .env (Phase 2 adds security)"
```

### After Phase 2:
```bash
git add src/utils/api_key_manager.py src/ui/api_config_ui.py analytics_dashboard.py src/data/
git commit -m "feat: Add API key security with macOS Keychain integration

- Recovered APIKeyManager from backup branch
- Recovered first-launch wizard UI
- Integrated wizard into dashboard startup
- Updated data collectors to use Keychain
- Fallback to .env for development mode

Production-ready with secure credential storage"
```

### After Phase 3:
```bash
git add docs/USER_INSTALLATION_GUIDE_v0.2.md
git commit -m "docs: Add professional DMG and installation guide

- Created professional DMG with Applications shortcut
- Added comprehensive user installation guide
- Updated documentation for v0.2.0 release"
```

---

## Rollback Plan

If Phase 1 fails:
```bash
# Revert changes
git reset --hard HEAD

# We're still at clean state (7888d1f + case-insensitive search fix)
# Can try alternative approaches or debug issues
```

If Phase 2 fails:
```bash
# Keep Phase 1 (working bundle)
# Remove Phase 2 files
rm src/utils/api_key_manager.py src/ui/api_config_ui.py

# Revert collector changes
git checkout src/data/
```

---

## Success Criteria

### Phase 1 Success:
✅ DMG opens and launches Streamlit
✅ Dashboard displays correctly
✅ All features work (search, analysis, etc.)
⚠️ Still requires .env file (not secure for distribution)

### Phase 2 Success:
✅ First launch shows key configuration wizard
✅ Keys save to macOS Keychain
✅ Dashboard works with user-provided keys
✅ No .env file needed in bundle
✅ Production-ready for distribution

### Phase 3 Success:
✅ Professional DMG with drag-to-Applications
✅ Clear installation guide
✅ App icon (optional but nice)
✅ Ready to share with users

---

## Timeline Estimate

| Task | Time | Cumulative |
|------|------|------------|
| Phase 1.1: Modify dashboard | 15 min | 15 min |
| Phase 1.2: Create spec | 15 min | 30 min |
| Phase 1.3-1.4: Build & test | 30 min | 1 hr |
| Phase 1.5: Create DMG | 5 min | 1 hr 5 min |
| **Phase 1 Total** | **1-2 hrs** | |
| Phase 2.1: Recover files | 10 min | 10 min |
| Phase 2.2: Integrate wizard | 30 min | 40 min |
| Phase 2.3: Update collectors | 45 min | 1 hr 25 min |
| Phase 2.4-2.5: Rebuild & test | 30 min | 1 hr 55 min |
| **Phase 2 Total** | **2-3 hrs** | |
| Phase 3: Polish & docs | 1 hr | 1 hr |
| **TOTAL** | **4-6 hrs** | |

---

## Next Session Checklist

1. [ ] Read this document
2. [ ] Verify backup branch exists
3. [ ] Start with Phase 1.1
4. [ ] Test after each step
5. [ ] Commit after each phase
6. [ ] Update CLAUDE.md when complete

---

**Prepared by:** Claude Code Assistant
**Last Updated:** November 24, 2025
**Status:** Ready to implement in next session
