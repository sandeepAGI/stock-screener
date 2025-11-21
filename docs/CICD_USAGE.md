# CI/CD Pipeline - Usage Guide

**Automated Build and Release System for StockAnalyzer Pro**

---

## 📋 Overview

The CI/CD pipeline automates the process of:
- ✅ Running security checks (no API keys in code)
- ✅ Running all tests
- ✅ Building the macOS application
- ✅ Creating DMG installers
- ✅ Publishing GitHub Releases
- ✅ Promoting main to prod

---

## 🔄 Workflows

### 1. **Test on Main** (`test-on-main.yml`)
**Trigger:** Automatic on every push/PR to `main`

**Purpose:** Ensure code quality on the main development branch

**Steps:**
1. Security verification (no API keys)
2. Run all tests on macOS

**When it runs:**
- Every push to `main` branch
- Every pull request to `main`
- Manual trigger via Actions tab

---

### 2. **Promote to Prod** (`promote-to-prod.yml`)
**Trigger:** Manual only

**Purpose:** Promote tested code from main to prod and trigger release

**Steps:**
1. Verify all tests pass on main
2. Run security checks
3. Merge main → prod
4. Create version tag
5. Trigger build workflow automatically

**How to use:**

#### Via GitHub UI:
1. Go to **Actions** tab
2. Select **"Promote Main to Prod"** workflow
3. Click **"Run workflow"**
4. Fill in:
   - **Version:** `v1.0.0` (semantic version)
   - **Create Release:** Check if you want automatic release
5. Click **"Run workflow"**

#### Via Command Line:
```bash
# Using GitHub CLI
gh workflow run promote-to-prod.yml \
  -f version=v1.0.0 \
  -f create_release=true
```

---

### 3. **Build and Release** (`build-release.yml`)
**Trigger:** Automatic on prod branch or version tags

**Purpose:** Build macOS app, create DMG, and publish release

**Steps:**
1. Security verification
2. Run all tests
3. Build macOS application with PyInstaller
4. Verify no API keys in built app
5. Create DMG installer
6. Upload artifacts
7. Create GitHub Release (if tagged)

**When it runs:**
- Push to `prod` branch
- Push of version tags (`v*.*.*`)
- Manual trigger via Actions tab

**Outputs:**
- `StockAnalyzer-macOS-v*.*.*.dmg` (downloadable from Releases)
- Build artifacts (available for 30 days)

---

## 🚀 Complete Release Workflow

### **Option A: Automated Release (Recommended)**

```bash
# 1. Develop on main branch
git checkout main
# ... make changes ...
git add .
git commit -m "feat: add new feature"
git push origin main

# 2. Verify tests pass
# Check Actions tab - "Test on Main" should pass

# 3. Promote to prod via GitHub UI
# Actions → Promote Main to Prod → Run workflow
# Enter version: v1.0.0
# Check "Create Release"
# Click "Run workflow"

# 4. Wait for automation
# - Main merges to prod
# - Tag is created
# - Build workflow triggers
# - DMG is created
# - GitHub Release is published

# 5. Done! ✨
# Your release is live at:
# https://github.com/yourusername/stock-outlier/releases
```

### **Option B: Manual Release**

```bash
# 1. Checkout prod and merge main
git checkout prod
git merge main

# 2. Create and push tag
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin prod
git push origin v1.0.0

# 3. Build workflow triggers automatically
# Check Actions tab for build progress

# 4. Download DMG from Artifacts or Release
```

---

## 📊 Workflow Visualization

```
┌─────────────┐
│   Develop   │
│  on main    │
└──────┬──────┘
       │
       │ Every push/PR
       ▼
┌─────────────────┐
│ Test on Main    │
│ ✓ Security      │
│ ✓ All tests     │
└─────────────────┘
       │
       │ Manual: "Promote to Prod"
       ▼
┌─────────────────┐
│ Promote to Prod │
│ ✓ Verify tests  │
│ ✓ Merge → prod  │
│ ✓ Create tag    │
└──────┬──────────┘
       │
       │ Automatic trigger
       ▼
┌─────────────────┐
│ Build & Release │
│ ✓ Build macOS   │
│ ✓ Create DMG    │
│ ✓ Publish       │
└─────────────────┘
```

---

## 🔐 Security Checks

Every workflow includes security verification:

### **Checks Performed:**
- ✅ No Reddit API client ID in code
- ✅ No Reddit API client secret in code
- ✅ No Claude API keys in code (pattern match)
- ✅ No `.env` file committed
- ✅ `.env.example` contains no real keys
- ✅ Built app contains no API keys

### **If Security Check Fails:**
The workflow stops immediately and shows which check failed.

**Fix it by:**
1. Remove the API key from code
2. Add to `.gitignore` if it's a file
3. Push the fix to main
4. Re-run the workflow

---

## 📦 Artifacts

### **Build Artifacts (Available for 30 days):**
- `StockAnalyzer-macOS-v*.*.*.dmg` - DMG installer
- `StockAnalyzer.app` - Application bundle
- Build logs and reports

**Download artifacts:**
1. Go to Actions tab
2. Click on the workflow run
3. Scroll to **Artifacts** section
4. Download the artifact

### **Release Artifacts (Permanent):**
When a release is created, the DMG is attached to:
- GitHub Releases page
- Accessible via direct URL
- Includes release notes

---

## 🔧 Configuration

### **Secrets Required:**
None! The workflow uses:
- `GITHUB_TOKEN` - Automatically provided by GitHub

### **Optional Configuration:**

#### Custom DMG Icon:
Add icon to workflow in `build-release.yml`:
```yaml
- name: Create DMG installer
  run: |
    # Add --icon flag if you have an icon file
    hdiutil create -volname "StockAnalyzer Pro" \
      -srcfolder dist/StockAnalyzer.app \
      -ov -format UDZO \
      "$DMG_NAME"
```

#### Notifications:
Add notification step to `notify` job:
```yaml
- name: Send notification
  uses: some-notification-action
  with:
    message: "Build completed!"
```

---

## 🐛 Troubleshooting

### **Problem: Security check fails**
**Solution:**
```bash
# Run security check locally
grep -r "yeKIESP30pvI8o9ZU9JLBg" --exclude-dir=.git .
grep -r "sk-ant-api03-" --exclude-dir=.git --exclude="*.example" .

# Remove any found keys
# Commit and push
```

### **Problem: Tests fail on CI**
**Solution:**
```bash
# Run tests locally first
python -m pytest tests/ -v

# Fix failing tests
# Commit and push
```

### **Problem: Build fails**
**Solution:**
1. Check build logs in Actions tab
2. Look for missing dependencies
3. Update `StockAnalyzer.spec` if needed
4. Test build locally:
   ```bash
   pyinstaller StockAnalyzer.spec
   ```

### **Problem: DMG not created**
**Solution:**
- Check that `StockAnalyzer.app` was built successfully
- Verify `hdiutil` command syntax in workflow
- Check macOS runner logs

---

## 📝 Version Numbering

**Semantic Versioning:** `vMAJOR.MINOR.PATCH`

### Examples:
- `v1.0.0` - Initial release
- `v1.0.1` - Bug fix
- `v1.1.0` - New feature (backward compatible)
- `v2.0.0` - Breaking change

### **Choosing Version Numbers:**

| Change Type | Version | Example |
|-------------|---------|---------|
| Bug fix | Patch | v1.0.0 → v1.0.1 |
| New feature | Minor | v1.0.1 → v1.1.0 |
| Breaking change | Major | v1.1.0 → v2.0.0 |
| Initial release | Major | v1.0.0 |

---

## 📊 Monitoring Builds

### **View Build Status:**
1. Go to **Actions** tab in GitHub
2. See all workflow runs
3. Click on a run to see details
4. Green checkmark = success
5. Red X = failure

### **Build Notifications:**
GitHub sends email notifications for:
- Failed builds (if you're watching the repo)
- Completed releases

### **Build Logs:**
- Available for 90 days
- Download from Actions tab
- Useful for debugging

---

## 🎯 Best Practices

### **Before Promoting to Prod:**
1. ✅ All tests pass on main
2. ✅ Feature is complete and tested
3. ✅ Documentation is updated
4. ✅ CHANGELOG.md is updated
5. ✅ Version number is decided

### **Release Notes:**
The workflow auto-generates release notes, but you can customize them:

1. Edit `.github/workflows/build-release.yml`
2. Modify the `Generate release notes` step
3. Add custom notes for each release

### **Testing Releases:**
1. Download the DMG from artifacts first
2. Test on a clean Mac if possible
3. Verify first-launch wizard works
4. Test data collection and analysis
5. Only then create public release

---

## 🔄 Hotfix Workflow

For urgent fixes that need to go to prod immediately:

```bash
# 1. Create hotfix branch from prod
git checkout prod
git checkout -b hotfix/critical-bug

# 2. Fix the bug
# ... make changes ...
git commit -m "fix: critical bug"

# 3. Merge to both prod and main
git checkout prod
git merge hotfix/critical-bug
git push origin prod

git checkout main
git merge hotfix/critical-bug
git push origin main

# 4. Tag the hotfix
git tag -a v1.0.1 -m "Hotfix v1.0.1"
git push origin v1.0.1

# 5. Build triggers automatically
```

---

## 📖 Quick Reference

### **Commands:**

```bash
# View workflow status
gh workflow list

# Trigger promote-to-prod
gh workflow run promote-to-prod.yml -f version=v1.0.0

# View recent runs
gh run list

# View specific run
gh run view <run-id>

# Download artifacts
gh run download <run-id>
```

### **URLs:**
- **Actions:** `https://github.com/USERNAME/REPO/actions`
- **Releases:** `https://github.com/USERNAME/REPO/releases`
- **Latest Release:** `https://github.com/USERNAME/REPO/releases/latest`

---

## 🚀 Summary

**To release a new version:**

1. **Develop** on `main` branch
2. **Test** automatically on every push
3. **Promote** via "Promote to Prod" workflow
4. **Build** happens automatically
5. **Release** is created automatically
6. **Distribute** via GitHub Releases

**That's it!** The entire process is automated. 🎉

---

**Last Updated:** November 20, 2025
**Pipeline Version:** 1.0
**Platforms:** macOS
