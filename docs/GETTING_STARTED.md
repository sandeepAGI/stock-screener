# Getting Started with StockAnalyzer Pro

**Complete guide for developers**

---

## 📋 Prerequisites

### Required Software:
- **macOS:** 10.13 or later
- **Python:** 3.12 or later
- **Git:** For version control
- **GitHub Account:** For CI/CD and releases

### Optional but Recommended:
- **GitHub CLI** (`gh`): For workflow management
- **Homebrew:** For installing tools
- **VS Code** or **PyCharm:** For development

---

## ⚡ Quick Setup (5 minutes)

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/stock-outlier.git
cd stock-outlier
```

### 2. Install Dependencies
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install PyInstaller for building
pip install pyinstaller
```

### 3. Set Up API Keys (for development)
```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API keys
# Use nano, vim, or any text editor
nano .env
```

**Add your keys:**
```bash
REDDIT_CLIENT_ID=your_reddit_client_id_here
REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
REDDIT_USER_AGENT=StockAnalyzer:v1.0 (by /u/your_username)
NEWS_API_KEY=your_claude_api_key_here
```

### 4. Run the Dashboard
```bash
streamlit run analytics_dashboard.py
```

**Your browser should open to:** `http://localhost:8501`

---

## 🧪 Running Tests

### Run All Tests:
```bash
python -m pytest tests/ -v
```

### Run Specific Test Files:
```bash
# API Key Manager tests
python -m pytest tests/test_api_key_manager.py -v

# Integration tests
python -m pytest tests/test_phase2_integration.py -v
```

### Expected Results:
- ✅ **38/38 tests passing**
- ⏱️ **Execution time:** ~10-15 seconds

---

## 🔨 Development Workflow

### 1. Create a Feature Branch
```bash
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
```

###2. Make Your Changes
```bash
# Edit code
# Add tests
# Update documentation
```

### 3. Test Your Changes
```bash
# Run tests
python -m pytest tests/ -v

# Run security check
grep -r "sk-ant-api03-" --exclude="*.example" .

# Test dashboard
streamlit run analytics_dashboard.py
```

### 4. Commit and Push
```bash
git add .
git commit -m "feat: description of your feature"
git push origin feature/your-feature-name
```

### 5. Create Pull Request
1. Go to GitHub repository
2. Click "Pull requests" → "New pull request"
3. Select your branch
4. Fill in description
5. Submit for review

### 6. After Merge to Main
Tests will run automatically via GitHub Actions.

---

## 📦 Building the Application

### Local Build (for testing):

```bash
# 1. Clean previous builds
rm -rf build/ dist/

# 2. Run tests
python -m pytest tests/ -v

# 3. Build with PyInstaller
pyinstaller StockAnalyzer.spec

# 4. Verify build
ls -lh dist/StockAnalyzer.app

# 5. Test the application
open dist/StockAnalyzer.app

# Or run from terminal to see output:
./dist/StockAnalyzer.app/Contents/MacOS/StockAnalyzer
```

**Build time:** 5-10 minutes
**Output size:** ~200-300 MB

### Verify Security:
```bash
# Check for API keys in built app
cd dist/
grep -r "yeKIESP30pvI8o9ZU9JLBg" StockAnalyzer.app || echo "✓ No Reddit keys"
grep -r "sk-ant-api03" StockAnalyzer.app || echo "✓ No Claude keys"
```

### Create DMG:
```bash
cd ..
hdiutil create -volname "StockAnalyzer Pro" \
  -srcfolder dist/StockAnalyzer.app \
  -ov -format UDZO \
  StockAnalyzer-macOS-v1.0.0.dmg

# Verify DMG created
ls -lh *.dmg
```

---

## 🚀 Using CI/CD for Releases

### Automated Release (Recommended):

**Step 1:** Develop on main branch
```bash
git checkout main
# ... make changes ...
git commit -m "feat: new feature"
git push origin main
```

**Step 2:** Wait for tests to pass
- Check **Actions** tab in GitHub
- "Test on Main" workflow should pass ✅

**Step 3:** Promote to production
Via GitHub UI:
1. Go to **Actions** tab
2. Click **"Promote Main to Prod"**
3. Click **"Run workflow"**
4. Enter version: `v1.0.0`
5. Check "Create Release"
6. Click **"Run workflow"**

Via Command Line:
```bash
gh workflow run promote-to-prod.yml -f version=v1.0.0 -f create_release=true
```

**Step 4:** Wait for automation (~15 minutes)
- Main merges to prod ✅
- Tag created ✅
- App builds ✅
- DMG created ✅
- Release published ✅

**Step 5:** Share the release
Get the URL: `https://github.com/yourusername/stock-outlier/releases/latest`

---

## 📂 Project Structure

```
stock-outlier/
├── .github/
│   └── workflows/           # CI/CD pipelines
│       ├── test-on-main.yml
│       ├── promote-to-prod.yml
│       └── build-release.yml
├── src/
│   ├── calculations/        # Score calculators
│   │   ├── fundamental.py
│   │   ├── quality.py
│   │   ├── growth.py
│   │   ├── sentiment.py
│   │   └── composite.py
│   ├── data/               # Data collection
│   │   ├── collectors.py
│   │   ├── database.py
│   │   ├── sentiment_analyzer.py
│   │   ├── bulk_sentiment_processor.py
│   │   └── unified_bulk_processor.py
│   ├── ui/                 # UI components
│   │   ├── __init__.py
│   │   └── api_config_ui.py
│   └── utils/              # Utilities
│       ├── api_key_manager.py
│       └── helpers.py
├── tests/                  # Test suite
│   ├── test_api_key_manager.py
│   └── test_phase2_integration.py
├── utilities/              # CLI tools
│   ├── smart_refresh.py
│   └── batch_monitor.py
├── docs/                   # Documentation
├── analytics_dashboard.py  # Main dashboard
├── launcher_macos.py       # macOS launcher
├── StockAnalyzer.spec      # PyInstaller config
├── requirements.txt        # Dependencies
└── .env.example           # Environment template
```

---

## 🔐 Security Best Practices

### API Keys:
1. **NEVER commit .env** to git
2. **NEVER hardcode** API keys in code
3. **ALWAYS use** `.env.example` for templates
4. **VERIFY** no keys in builds before distribution

### Verification Commands:
```bash
# Check .gitignore includes .env
cat .gitignore | grep ".env"

# Verify .env is ignored
git check-ignore .env

# Check for accidental key commits
git log --all --full-history --source --extra=all -- .env
```

### Before Each Release:
```bash
# Run security verification
grep -r "yeKIESP30pvI8o9ZU9JLBg" --exclude-dir=.git .
grep -r "sk-ant-api03-" --exclude-dir=.git --exclude="*.example" .
```

Both should return no results! ✅

---

## 🐛 Troubleshooting

### Tests Fail:
```bash
# Check Python version
python --version  # Should be 3.12+

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Clear pytest cache
rm -rf .pytest_cache

# Run tests with more verbosity
python -m pytest tests/ -vv
```

### Dashboard Won't Start:
```bash
# Check if port is in use
lsof -i :8501

# Kill existing Streamlit processes
pkill -f streamlit

# Try different port
streamlit run analytics_dashboard.py --server.port 8502
```

### Build Fails:
```bash
# Clean build directories
rm -rf build/ dist/

# Verify PyInstaller installation
pip show pyinstaller

# Try building with debug mode
pyinstaller StockAnalyzer.spec --debug all
```

### Import Errors:
```bash
# Ensure project root is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or install in development mode
pip install -e .
```

---

## 📝 Common Tasks

### Update Dependencies:
```bash
# Update requirements.txt
pip freeze > requirements.txt

# Or manually edit requirements.txt
# Then install
pip install -r requirements.txt
```

### Collect Data:
```bash
# Collect all data types for all stocks
python utilities/smart_refresh.py --data-types all

# Collect for specific stocks
python utilities/smart_refresh.py --symbols AAPL MSFT --data-types fundamentals

# Process sentiment
python utilities/smart_refresh.py --process-sentiment --poll
```

### Database Operations:
```bash
# Backup database
python utilities/backup_database.py

# Check database status
sqlite3 data/stock_data.db "SELECT COUNT(*) FROM stocks"
```

### View Logs:
```bash
# Streamlit logs
tail -f ~/.streamlit/logs/streamlit.log

# Application logs (if configured)
tail -f logs/app.log
```

---

## 🎓 Learning Resources

### Documentation:
- [Streamlit Docs](https://docs.streamlit.io/)
- [PyInstaller Manual](https://pyinstaller.org/)
- [GitHub Actions](https://docs.github.com/en/actions)
- [Anthropic API](https://docs.anthropic.com/)

### Internal Guides:
- `docs/BUILD_AND_DISTRIBUTE.md` - Building guide
- `docs/CICD_USAGE.md` - CI/CD pipeline
- `docs/USER_INSTALLATION_GUIDE.md` - User guide
- `METHODS.md` - Scoring methodology

---

## ✅ Checklist for New Contributors

Before your first commit:
- [ ] Cloned repository
- [ ] Installed dependencies
- [ ] Set up `.env` file
- [ ] Run dashboard successfully
- [ ] All tests passing (38/38)
- [ ] Read `CLAUDE.md`
- [ ] Created feature branch
- [ ] Understand git workflow

Before your first PR:
- [ ] Tests added for new features
- [ ] Documentation updated
- [ ] Security check passed
- [ ] Code follows existing patterns
- [ ] Commit messages clear

---

## 🚀 Next Steps

1. **Explore the codebase:**
   - Read `src/calculations/` for scoring logic
   - Check `src/data/` for data collection
   - Review `analytics_dashboard.py` for UI

2. **Try building locally:**
   - Follow the build steps above
   - Test the built application
   - Verify it works without Python

3. **Set up CI/CD:**
   - Push workflows to GitHub
   - Trigger a test run
   - Try the automated release flow

4. **Make your first contribution:**
   - Pick a small feature or bug fix
   - Create a branch and PR
   - Go through the review process

---

**Questions?** Check the [docs/](.) folder or open a GitHub Discussion!

**Ready to build?** See [BUILD_AND_DISTRIBUTE.md](BUILD_AND_DISTRIBUTE.md)

**Ready to release?** See [CICD_USAGE.md](CICD_USAGE.md)

---

**Last Updated:** November 20, 2025
**Version:** 1.0.0
