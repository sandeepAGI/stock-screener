# CI/CD Quick Reference Card

**StockAnalyzer Pro - Automated Build & Release**

---

## 🚀 Quick Release Process

```bash
# 1. Develop on main
git checkout main
git add .
git commit -m "feat: your feature"
git push

# 2. Promote to prod (via GitHub UI)
Actions → Promote Main to Prod → Run workflow
  Version: v1.0.0
  ✓ Create Release

# 3. Wait ~10 minutes

# 4. Done! Release at:
# github.com/USERNAME/REPO/releases
```

---

## 📋 Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| **Test on Main** | Every push to `main` | Run tests |
| **Promote to Prod** | Manual | Merge main→prod + tag |
| **Build & Release** | Push to `prod` or tag | Build DMG + Release |

---

## ⚡ Common Commands

### Via GitHub CLI:
```bash
# Promote to prod
gh workflow run promote-to-prod.yml -f version=v1.0.0

# Check status
gh run list

# Download latest artifact
gh run download
```

### Via GitHub UI:
1. **Actions tab** → Select workflow → **Run workflow**
2. Enter version number
3. Click **Run workflow**

---

## 🔐 Security Checks

Every build verifies:
- ✅ No API keys in code
- ✅ No `.env` file committed
- ✅ Built app contains no keys

---

## 📦 Outputs

### Artifacts (30 days):
- DMG installer
- App bundle
- Build logs

### Releases (permanent):
- DMG attached
- Auto-generated notes
- Downloadable

---

## 🐛 Quick Fixes

**Tests fail?**
```bash
python -m pytest tests/ -v
```

**Security fail?**
```bash
grep -r "sk-ant-api03-" --exclude="*.example" .
```

**Build fail?**
```bash
pyinstaller StockAnalyzer.spec
```

---

## 📝 Version Numbers

- Bug fix: `v1.0.0` → `v1.0.1`
- New feature: `v1.0.1` → `v1.1.0`
- Breaking: `v1.1.0` → `v2.0.0`

---

## 🎯 Hotfix

```bash
git checkout prod
git checkout -b hotfix/urgent

# Fix bug
git commit -m "fix: urgent bug"

git checkout prod
git merge hotfix/urgent
git push

git tag -a v1.0.1 -m "Hotfix"
git push origin v1.0.1
```

---

**Full docs:** `docs/CICD_USAGE.md`
