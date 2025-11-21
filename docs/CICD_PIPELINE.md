# CI/CD Pipeline Documentation
**StockAnalyzer Pro - Automated Build & Release System**

**Last Updated:** November 20, 2025
**Status:** Documentation Complete - Ready for Implementation

---

## 📋 Table of Contents
1. [Overview](#overview)
2. [Branching Strategy](#branching-strategy)
3. [GitHub Actions Workflow](#github-actions-workflow)
4. [Build Process](#build-process)
5. [Release Process](#release-process)
6. [Upgrade Workflow](#upgrade-workflow)
7. [Implementation Checklist](#implementation-checklist)

---

## 🎯 Overview

### **Purpose**
Automate the building and distribution of StockAnalyzer Pro as standalone executables for macOS, Windows, and Linux, eliminating the need for users to install Python or run terminal commands.

### **Architecture**
```
Development (main branch)
    ├─ Feature development
    ├─ Bug fixes
    ├─ Testing
    └─ Merge to prod when stable
         ↓
Production (prod branch)
    ├─ Trigger GitHub Actions
    ├─ Build executables (macOS, Windows, Linux)
    ├─ Run automated tests
    ├─ Create GitHub Release
    └─ Publish downloadable artifacts
```

### **Key Benefits**
✅ **Automated Builds**: Push to prod → executables built automatically
✅ **Cross-Platform**: Single pipeline builds for all OS platforms
✅ **Version Control**: Semantic versioning with git tags (v1.0.0, v1.1.0)
✅ **Quality Gates**: Automated testing before release
✅ **Distribution**: GitHub Releases for easy sharing
✅ **Rollback Safety**: Keep prod stable, experiment on main

---

## 🌿 Branching Strategy

### **Two-Branch Model**

#### **`main` Branch (Development)**
- **Purpose**: Active development and testing
- **Updates**: Frequent commits, feature additions, bug fixes
- **Stability**: May contain experimental features
- **CI/CD**: Optional - can run tests on every push
- **Protection**: None (free development)

#### **`prod` Branch (Production)**
- **Purpose**: Stable releases only
- **Updates**: Merged from main when ready for release
- **Stability**: Production-ready code only
- **CI/CD**: Triggers full build pipeline
- **Protection**: Protected branch (require PR approval - optional)

### **Workflow Diagram**
```
main branch:     A───B───C───D───E───F───G
                          \           \
prod branch:               v1.0.0      v1.1.0
                          (release)   (release)
```

---

## 🤖 GitHub Actions Workflow

### **Trigger Events**

**1. Push to prod branch**
```yaml
on:
  push:
    branches:
      - prod
```
- Automatically builds when code is merged/pushed to prod
- Creates artifacts but no GitHub Release

**2. Version tag creation**
```yaml
on:
  push:
    tags:
      - 'v*'
```
- Builds AND creates GitHub Release
- Example: `git tag v1.2.0 && git push --tags`

**3. Manual trigger**
```yaml
on:
  workflow_dispatch:
```
- Run workflow manually from GitHub UI
- Useful for debugging or rebuilding

### **Jobs Overview**

The workflow consists of 4 parallel jobs + 1 final job:

```
┌─────────────────┐
│  build-macos    │  → macOS .app + DMG installer
├─────────────────┤
│  build-windows  │  → Windows .exe + installer
├─────────────────┤
│  build-linux    │  → Linux binary + AppImage
└─────────────────┘
         ↓
┌─────────────────┐
│ create-release  │  → Publishes to GitHub Releases
└─────────────────┘
```

---

## 🔨 Build Process

### **Build Strategy: PyInstaller**

**Why PyInstaller?**
- ✅ Bundles Python interpreter + dependencies
- ✅ Creates standalone executables
- ✅ Cross-platform support
- ✅ Handles complex dependencies (Streamlit, Plotly, SQLite)
- ✅ Widely used and well-documented

### **Platform-Specific Builds**

#### **macOS Build**
```bash
# Runner: macos-latest (macOS 12+)
# Output: StockAnalyzer.app (macOS application bundle)
# Packaged as: DMG installer

pyinstaller --name "StockAnalyzer" \
            --windowed \                    # No terminal window
            --icon=assets/icon.icns \       # macOS icon
            --add-data "src:src" \          # Bundle source code
            --add-data "analytics_dashboard.py:." \
            --hidden-import=streamlit \     # Ensure Streamlit included
            --hidden-import=plotly \        # Ensure Plotly included
            launcher_macos.py

# Create DMG installer
hdiutil create -volname "StockAnalyzer" \
               -srcfolder dist/StockAnalyzer.app \
               -ov -format UDZO \
               StockAnalyzer-macOS.dmg
```

**User Experience:**
1. Download DMG file
2. Double-click to mount
3. Drag app to Applications folder
4. Double-click to launch

#### **Windows Build**
```bash
# Runner: windows-latest (Windows Server 2022)
# Output: StockAnalyzer.exe
# Packaged as: ZIP or installer (NSIS/Inno Setup)

pyinstaller --name "StockAnalyzer" `
            --windowed `                    # No console window
            --icon=assets/icon.ico `        # Windows icon
            --add-data "src;src" `          # Note: semicolon on Windows
            --add-data "analytics_dashboard.py;." `
            --hidden-import=streamlit `
            --hidden-import=plotly `
            launcher_windows.py
```

**User Experience:**
1. Download ZIP file
2. Extract to desired location
3. Double-click StockAnalyzer.exe

#### **Linux Build**
```bash
# Runner: ubuntu-latest (Ubuntu 22.04)
# Output: StockAnalyzer (binary)
# Packaged as: tar.gz or AppImage

pyinstaller --name "StockAnalyzer" \
            --onefile \                     # Single executable
            --add-data "src:src" \
            --add-data "analytics_dashboard.py:." \
            --hidden-import=streamlit \
            --hidden-import=plotly \
            launcher_linux.py
```

**User Experience:**
1. Download tar.gz
2. Extract: `tar -xzf StockAnalyzer-Linux.tar.gz`
3. Run: `./StockAnalyzer`

### **What Gets Bundled**

**Included:**
- ✅ Python 3.11 interpreter
- ✅ All dependencies (Streamlit, Plotly, Pandas, etc.)
- ✅ Source code (`src/` directory)
- ✅ Dashboard UI (`analytics_dashboard.py`)
- ✅ Launcher script
- ✅ Empty database schema

**Excluded:**
- ❌ `.env` files (security - API keys not bundled)
- ❌ Existing database data (users create their own)
- ❌ Git history / version control files
- ❌ Development dependencies (pytest, black, etc.)

### **Artifact Storage**

**During Build:**
```yaml
- name: Upload artifact
  uses: actions/upload-artifact@v3
  with:
    name: StockAnalyzer-macOS
    path: StockAnalyzer-macOS.dmg
```

**Artifacts stored for:**
- 90 days by default (configurable)
- Available for download from GitHub Actions tab
- Used by `create-release` job if creating GitHub Release

---

## 📦 Release Process

### **Creating a Release**

**Step 1: Develop and Test on main**
```bash
git checkout main
# ... develop features ...
git add .
git commit -m "feat: Add portfolio tracking feature"
git push origin main
```

**Step 2: Merge to prod**
```bash
git checkout prod
git merge main
git push origin prod
```
→ Triggers workflow, builds executables, uploads artifacts (no release yet)

**Step 3: Tag for Release**
```bash
git tag -a v1.2.0 -m "Release v1.2.0 - Portfolio tracking"
git push origin v1.2.0
```
→ Triggers workflow again, creates GitHub Release with artifacts

### **GitHub Release Creation**

```yaml
- name: Create Release
  uses: softprops/action-gh-release@v1
  with:
    files: |
      StockAnalyzer-macOS/StockAnalyzer-macOS.dmg
      StockAnalyzer-Windows/StockAnalyzer-Windows.zip
      StockAnalyzer-Linux/StockAnalyzer-Linux.tar.gz
    draft: false
    prerelease: false
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**Result:**
- GitHub Releases page shows new release (v1.2.0)
- All three platform builds attached and downloadable
- Release notes can be auto-generated from commits
- Users get notification if watching repository

### **Semantic Versioning**

Format: `vMAJOR.MINOR.PATCH`

**Examples:**
- `v1.0.0` - Initial production release
- `v1.1.0` - New feature added (minor version bump)
- `v1.1.1` - Bug fix (patch version bump)
- `v2.0.0` - Breaking changes (major version bump)

**When to Bump:**
- **MAJOR**: Breaking changes (API changes, major refactor)
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, small improvements

---

## 🔄 Upgrade Workflow

### **Scenario: New Feature Development**

**Timeline:**
```
Week 1-2: Development on main
├─ Day 1: Implement feature
├─ Day 3: Add tests
├─ Day 5: Fix bugs
└─ Day 10: Feature complete

Week 3: Release
├─ Day 1: Merge main → prod
├─ Day 2: Test prod build locally
├─ Day 3: Create release tag (v1.2.0)
└─ Day 3: GitHub Actions builds & publishes
```

**Commands:**
```bash
# Development (main branch)
git checkout main
git pull
# ... develop ...
git commit -m "feat: Add new scoring algorithm"
git push origin main

# When ready for release
git checkout prod
git pull
git merge main
git push origin prod

# Test the prod build (optional)
# Download artifact from GitHub Actions
# Test on your machine

# Create release
git tag -a v1.2.0 -m "Release v1.2.0 - New scoring algorithm"
git push origin prod --tags

# GitHub Actions automatically:
# 1. Builds macOS, Windows, Linux executables
# 2. Creates GitHub Release
# 3. Attaches downloadable files
```

### **Scenario: Hotfix**

**For critical bugs:**
```bash
# Option 1: Fix on main, merge to prod
git checkout main
# ... fix bug ...
git commit -m "fix: Critical calculation error"
git push origin main

git checkout prod
git merge main
git tag -a v1.2.1 -m "Hotfix: Calculation error"
git push origin prod --tags

# Option 2: Fix directly on prod (emergency only)
git checkout prod
# ... fix bug ...
git commit -m "fix: Critical security issue"
git tag -a v1.2.1 -m "Security hotfix"
git push origin prod --tags

# Then backport to main
git checkout main
git cherry-pick <commit-hash>
git push origin main
```

### **User Upgrade Experience**

**Current Users:**
1. Receive notification (if watching GitHub repo)
2. Visit GitHub Releases page
3. Download new version for their OS
4. Replace old app with new app
5. Database and settings preserved (stored separately)

**Automatic Updates (Future Enhancement):**
- App checks GitHub API for new releases on startup
- Prompts user to download update
- Could auto-download and install (advanced)

---

## ✅ Implementation Checklist

### **Phase 1: Repository Setup**
- [x] Create `prod` branch
- [ ] Set up branch protection rules (optional)
  ```
  Settings → Branches → Add rule
  - Branch name pattern: prod
  - Require pull request before merging
  - Require approvals: 1
  ```

### **Phase 2: Project Structure**
- [ ] Create launcher scripts
  - [ ] `launcher_macos.py`
  - [ ] `launcher_windows.py`
  - [ ] `launcher_linux.py`
- [ ] Create app icons
  - [ ] `assets/icon.icns` (macOS)
  - [ ] `assets/icon.ico` (Windows)
  - [ ] `assets/icon.png` (Linux)
- [ ] Create PyInstaller spec files (optional, for advanced config)
  - [ ] `stockanalyzer_macos.spec`
  - [ ] `stockanalyzer_windows.spec`
  - [ ] `stockanalyzer_linux.spec`

### **Phase 3: API Key Management**
- [ ] Implement user-provided API key system
  - [ ] Settings page in dashboard
  - [ ] Secure local storage (keyring/encrypted)
  - [ ] First-launch wizard
- [ ] Update `.env.example` with instructions
- [ ] Create user documentation for API setup

### **Phase 4: GitHub Actions Setup**
- [ ] Create `.github/workflows/build-release.yml`
- [ ] Test workflow on test branch first
- [ ] Verify artifacts are created correctly
- [ ] Test GitHub Release creation

### **Phase 5: Testing & Documentation**
- [ ] Test builds on all platforms
  - [ ] macOS (test on real Mac)
  - [ ] Windows (test on real Windows PC)
  - [ ] Linux (test on Ubuntu VM)
- [ ] Create user documentation
  - [ ] Installation guide
  - [ ] API key setup guide
  - [ ] Troubleshooting guide
- [ ] Update README.md with download links

### **Phase 6: First Release**
- [ ] Merge main → prod
- [ ] Create v1.0.0 tag
- [ ] Verify GitHub Actions completes successfully
- [ ] Download and test all artifacts
- [ ] Write release notes
- [ ] Share with Aileron partner

---

## 🔒 Security Considerations

### **API Keys - User-Provided Model**

**Problem:**
- Cannot bundle your API keys (users would consume your quota)
- Need secure storage on user's machine

**Solution:**
- First launch: prompt for API keys
- Store in OS keyring (macOS Keychain, Windows Credential Manager)
- Fallback: encrypted local file
- Never log or expose keys

**Implementation:**
```python
import keyring

# Store API key
keyring.set_password("StockAnalyzer", "claude_api_key", user_input)

# Retrieve API key
api_key = keyring.get_password("StockAnalyzer", "claude_api_key")
```

### **Database Security**
- User's database stored in user's home directory
- Not bundled with app (users create their own data)
- No network access to centralized database

### **Code Signing (Future)**
- **macOS**: Sign app with Apple Developer ID (prevents Gatekeeper warnings)
- **Windows**: Sign with code signing certificate (prevents SmartScreen warnings)
- **Cost**: ~$99/year (Apple), ~$200/year (Windows)
- **Benefit**: Professional trust indicators

---

## 📊 Build Metrics

**Expected Build Times:**
- macOS: 8-12 minutes
- Windows: 10-15 minutes
- Linux: 6-10 minutes
- Total pipeline: ~15-20 minutes

**Artifact Sizes:**
- macOS DMG: ~200-300 MB
- Windows ZIP: ~150-250 MB
- Linux tar.gz: ~150-250 MB

**GitHub Actions Limits:**
- Free tier: 2,000 minutes/month
- Each release consumes: ~30 minutes (all platforms)
- Can do ~60 releases/month on free tier

---

## 🚀 Advanced Enhancements (Future)

### **Automated Testing**
```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: pytest tests/
      # Only build if tests pass

  build-macos:
    needs: test
    # ... build steps ...
```

### **Multi-Architecture Builds**
- Apple Silicon (M1/M2): `macos-latest` includes arm64
- Windows ARM: `windows-latest-arm64` (when available)
- Linux ARM: Custom runners or QEMU

### **Auto-Update System**
```python
# Check for updates on app startup
latest_release = requests.get("https://api.github.com/repos/USER/REPO/releases/latest")
if latest_release.version > current_version:
    show_update_prompt()
```

### **Electron Wrapper**
- Wrap Streamlit in Electron for true native feel
- Hide browser chrome (no URL bar)
- Better OS integration
- Larger file size (~400 MB)

---

## 📚 References

**PyInstaller Documentation:**
- https://pyinstaller.org/en/stable/

**GitHub Actions Documentation:**
- https://docs.github.com/en/actions

**Streamlit Deployment:**
- https://docs.streamlit.io/knowledge-base/deploy

**Code Signing:**
- macOS: https://developer.apple.com/developer-id/
- Windows: https://learn.microsoft.com/en-us/windows/win32/seccrypto/cryptography-tools

---

## 🆘 Troubleshooting

**Build fails with "Module not found":**
- Add to `--hidden-import` in PyInstaller command
- Check requirements.txt includes all dependencies

**App won't start on macOS (Gatekeeper):**
- Right-click → Open (first time)
- Or: System Preferences → Security → Allow

**Windows SmartScreen warning:**
- Click "More info" → "Run anyway"
- Solution: Code signing certificate

**Large file size:**
- Expected - bundles entire Python runtime
- Can optimize with `--exclude-module` for unused dependencies

---

**Document Status:** ✅ Complete - Ready for Implementation
**Next Step:** Implement Phase 2 (Project Structure) - Create launcher scripts
