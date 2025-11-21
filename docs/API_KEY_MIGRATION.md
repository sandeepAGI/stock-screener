# API Key Migration Plan
**Converting from Bundled Keys to User-Provided Keys**

**Last Updated:** November 20, 2025
**Purpose:** Secure API key handling for app distribution

---

## 🎯 Current State Analysis

### **API Keys Currently in .env:**

| API Key | Purpose | Rate Limit/Cost | Risk Level |
|---------|---------|-----------------|------------|
| `REDDIT_CLIENT_ID` | Reddit API access | 60 req/min (shared) | ⚠️ HIGH |
| `REDDIT_CLIENT_SECRET` | Reddit API auth | 60 req/min (shared) | ⚠️ HIGH |
| `REDDIT_USER_AGENT` | Reddit API identification | N/A | 🔶 MEDIUM |
| `NEWS_API_KEY` (Claude) | Sentiment analysis | $0.002/request | 🔴 CRITICAL |

### **What Happens If Bundled:**

**Scenario 1: Reddit API**
- You share app with Aileron partner
- Partner runs Reddit sentiment collection
- Uses YOUR Reddit API credentials
- Hits YOUR rate limit (60/min)
- Attributes posts to YOUR Reddit account (/u/Sure-Archer417)

**Scenario 2: Claude API**
- Partner runs sentiment analysis on 50,000 articles
- Cost: 50,000 × $0.002 = $100
- **YOU get charged $100**
- Partner doesn't even know they're using your API

**Scenario 3: Multiple Users**
- If partner shares with their team (3-5 people)
- All using same Reddit credentials = rate limit chaos
- All using same Claude API = your bill multiplies

---

## ✅ Target State: User-Provided Keys

### **User Experience:**

**First Launch:**
```
┌─────────────────────────────────────────────────────────┐
│  🔑 API Configuration Required                          │
│                                                          │
│  StockAnalyzer needs API keys to collect data.         │
│  Each user provides their own keys (you pay for your   │
│  own API usage).                                        │
│                                                          │
│  ✅ Required for Full Functionality:                    │
│  • Reddit API (social sentiment)                        │
│  • Claude API (advanced sentiment analysis)            │
│                                                          │
│  Choose one:                                            │
│  [Set Up Now]  [Skip - Limited Features]              │
└─────────────────────────────────────────────────────────┘
```

**API Setup Wizard:**
```
┌─────────────────────────────────────────────────────────┐
│  Step 1/2: Reddit API Setup                            │
│                                                          │
│  1. Visit: https://www.reddit.com/prefs/apps           │
│  2. Click "Create App" or "Create Another App"         │
│  3. Choose type: "script"                              │
│  4. Fill in:                                           │
│     - Name: StockAnalyzer                              │
│     - Redirect URI: http://localhost:8080              │
│  5. Copy credentials below                             │
│                                                          │
│  Client ID:                                            │
│  ┌────────────────────────────────────────────────┐   │
│  │ yeKIESP30pvI8o9ZU9JLBg                          │   │
│  └────────────────────────────────────────────────┘   │
│                                                          │
│  Client Secret:                                        │
│  ┌────────────────────────────────────────────────┐   │
│  │ ••••••••••••••••••••••••••••••••                │   │
│  └────────────────────────────────────────────────┘   │
│                                                          │
│  [Open Reddit Apps Page]  [Test Connection]  [Next]   │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠️ Implementation Details

### **Storage Strategy (All Keys)**

```python
# Stored in OS keyring or encrypted file
{
    "reddit_client_id": "user's reddit client id",
    "reddit_client_secret": "user's reddit secret",
    "reddit_user_agent": "user's app identifier",
    "claude_api_key": "user's claude key",
    "news_api_key": "user's news api key (optional)"
}
```

### **Code Changes Required:**

**1. Update collectors.py:**

```python
# BEFORE (current - reads from .env)
class RedditCollector:
    def __init__(self):
        load_dotenv()
        self.reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),      # ❌ Bundled key
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),  # ❌ Bundled key
            user_agent=os.getenv('REDDIT_USER_AGENT')     # ❌ Bundled key
        )

# AFTER (user-provided)
class RedditCollector:
    def __init__(self, api_key_manager: APIKeyManager):
        # Get user's credentials
        client_id = api_key_manager.get_api_key('reddit_client_id')
        client_secret = api_key_manager.get_api_key('reddit_client_secret')
        user_agent = api_key_manager.get_api_key('reddit_user_agent')

        if not (client_id and client_secret and user_agent):
            raise ValueError("Reddit API credentials not configured")

        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
```

**2. Update sentiment_analyzer.py:**

```python
# BEFORE (current - reads from .env)
class SentimentAnalyzer:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv('NEWS_API_KEY')  # ❌ Bundled key
        self.client = Anthropic(api_key=api_key)

# AFTER (user-provided)
class SentimentAnalyzer:
    def __init__(self, api_key_manager: APIKeyManager):
        claude_key = api_key_manager.get_api_key('claude_api_key')

        if not claude_key:
            raise ValueError("Claude API key not configured")

        self.client = Anthropic(api_key=claude_key)
```

**3. Update DataCollectionOrchestrator:**

```python
# BEFORE
class DataCollectionOrchestrator:
    def __init__(self, db_manager):
        self.db = db_manager
        self.reddit_collector = RedditCollector()  # ❌ Uses .env
        self.sentiment_analyzer = SentimentAnalyzer()  # ❌ Uses .env

# AFTER
class DataCollectionOrchestrator:
    def __init__(self, db_manager, api_key_manager: APIKeyManager):
        self.db = db_manager
        self.api_keys = api_key_manager

        # Only initialize if user has configured API keys
        try:
            self.reddit_collector = RedditCollector(self.api_keys)
        except ValueError:
            self.reddit_collector = None  # Disabled
            print("⚠️ Reddit collection disabled - API keys not configured")

        try:
            self.sentiment_analyzer = SentimentAnalyzer(self.api_keys)
        except ValueError:
            # Fallback to basic sentiment
            self.sentiment_analyzer = BasicSentimentAnalyzer()
            print("⚠️ Using basic sentiment - Claude API not configured")
```

---

## 📋 Migration Checklist

### **Phase 1: Create API Key Management System**
- [ ] Create `src/utils/api_key_manager.py`
- [ ] Add dependencies to `requirements.txt`:
  ```
  keyring>=24.0.0
  cryptography>=41.0.0
  ```
- [ ] Test API key storage/retrieval on macOS
- [ ] Test API key storage/retrieval on Windows
- [ ] Test API key storage/retrieval on Linux

### **Phase 2: Update Data Collection Code**
- [ ] Update `RedditCollector` to accept APIKeyManager
- [ ] Update `SentimentAnalyzer` to accept APIKeyManager
- [ ] Update `DataCollectionOrchestrator` to use APIKeyManager
- [ ] Add graceful degradation (disable features if no keys)
- [ ] Update `UnifiedBulkProcessor` to accept API key parameter

### **Phase 3: Create UI Components**
- [ ] Create first-launch wizard
  - [ ] Welcome screen
  - [ ] Reddit API setup step
  - [ ] Claude API setup step
  - [ ] Confirmation screen
- [ ] Create Settings → API Configuration page
- [ ] Add API status indicators to dashboard
- [ ] Add "Test Connection" buttons for each API
- [ ] Add helpful links to API registration pages

### **Phase 4: Update Documentation**
- [ ] Create user guide: "How to Get Reddit API Keys"
- [ ] Create user guide: "How to Get Claude API Keys"
- [ ] Update README.md with API setup instructions
- [ ] Create troubleshooting guide for common API issues
- [ ] Update .env.example (remove real keys, add placeholders)

### **Phase 5: Security Cleanup**
- [ ] Remove real API keys from .env
- [ ] Add `.env` to `.gitignore` (if not already)
- [ ] Add `.stockanalyzer/` to `.gitignore`
- [ ] Add `credentials.enc` to `.gitignore`
- [ ] Audit codebase for any hardcoded keys
- [ ] Verify no API keys in git history (BFG Repo-Cleaner if needed)

### **Phase 6: Testing**
- [ ] Test first-launch wizard flow
- [ ] Test with invalid API keys (proper error messages)
- [ ] Test with valid Reddit keys
- [ ] Test with valid Claude keys
- [ ] Test with no API keys (graceful degradation)
- [ ] Test API key updates
- [ ] Test API key deletion
- [ ] Test on all platforms (macOS, Windows, Linux)

### **Phase 7: Distribution Prep**
- [ ] Create .env.example with empty placeholders
- [ ] Build executable (verify no real keys bundled)
- [ ] Extract and inspect bundled files
- [ ] Test executable on clean machine
- [ ] Document for Aileron partner

---

## 🧪 Testing Commands

### **Verify No Keys Bundled in Executable:**

```bash
# After building with PyInstaller
cd dist/StockAnalyzer/

# macOS/Linux: Search for API keys in bundled files
grep -r "yeKIESP30pvI8o9ZU9JLBg" .
grep -r "sk-ant-api03" .

# Windows: Use findstr
findstr /s /i "yeKIESP30pvI8o9ZU9JLBg" *
findstr /s /i "sk-ant-api03" *

# Should return NO results (keys not bundled)
```

### **Test API Key Manager:**

```python
# test_api_key_manager.py

from src.utils.api_key_manager import APIKeyManager

def test_reddit_keys():
    manager = APIKeyManager()

    # Save test credentials
    manager.save_api_key("reddit_client_id", "test_client_id")
    manager.save_api_key("reddit_client_secret", "test_secret")
    manager.save_api_key("reddit_user_agent", "TestApp:v1.0")

    # Retrieve
    assert manager.get_api_key("reddit_client_id") == "test_client_id"
    assert manager.get_api_key("reddit_client_secret") == "test_secret"

    # Delete
    manager.delete_api_key("reddit_client_id")
    assert manager.get_api_key("reddit_client_id") is None

def test_graceful_degradation():
    """Test app works without API keys"""
    manager = APIKeyManager()
    db = DatabaseManager()

    # Should work without raising exception
    orchestrator = DataCollectionOrchestrator(db, manager)

    # Reddit collector should be None
    assert orchestrator.reddit_collector is None

    # Sentiment should fall back to basic
    assert isinstance(orchestrator.sentiment_analyzer, BasicSentimentAnalyzer)
```

---

## 📖 User Documentation (For Aileron Partner)

### **Getting Your API Keys**

**Why Do I Need API Keys?**
- StockAnalyzer collects data from Reddit and uses Claude AI for analysis
- Each user provides their own API keys
- You control and pay for your own API usage
- Your data and quotas are separate from other users

**Cost Estimate:**
- **Reddit API:** FREE (60 requests/minute)
- **Claude API:** ~$1-5/month for typical usage
  - Sentiment analysis: $0.002 per article
  - ~50,000 articles = $100 (one-time for S&P 500)
  - Incremental updates: ~$1-5/month

### **Step-by-Step Setup:**

**1. Reddit API (Required for Social Sentiment)**

1. Go to: https://www.reddit.com/prefs/apps
2. Log in to your Reddit account (or create one)
3. Scroll to bottom, click "create another app..."
4. Fill in:
   - **name:** StockAnalyzer
   - **type:** Select "script"
   - **description:** Stock sentiment analysis tool
   - **about url:** (leave blank)
   - **redirect uri:** http://localhost:8080
5. Click "create app"
6. Copy your credentials:
   - **Client ID:** (14 characters under app name)
   - **Client Secret:** (27 characters, click "show")
7. Paste into StockAnalyzer when prompted

**2. Claude API (Required for Advanced Sentiment)**

1. Go to: https://console.anthropic.com/
2. Sign up for an account
3. Navigate to "API Keys" section
4. Click "Create Key"
5. Name it: "StockAnalyzer"
6. Copy the key (starts with `sk-ant-api03-`)
7. Paste into StockAnalyzer when prompted

**Your API keys are stored securely on YOUR machine and never shared.**

---

## 🔒 Security Verification

### **For Developer (Before Sharing App):**

**Checklist:**
- [ ] Real API keys removed from .env
- [ ] .env not committed to git
- [ ] API keys not in git history
- [ ] Built executable doesn't contain keys
- [ ] APIKeyManager implementation tested
- [ ] First-launch wizard tested
- [ ] Documentation provided to user

### **Verification Script:**

```bash
#!/bin/bash
# verify_no_keys.sh - Run before distribution

echo "🔍 Checking for API keys in codebase..."

# Check for Reddit keys
if grep -r "yeKIESP30pvI8o9ZU9JLBg" --exclude-dir=.git .; then
    echo "❌ FAIL: Found Reddit Client ID in codebase"
    exit 1
fi

# Check for Claude keys
if grep -r "sk-ant-api03" --exclude-dir=.git .; then
    echo "❌ FAIL: Found Claude API key in codebase"
    exit 1
fi

# Check .env.example is clean
if grep -E "(yeKIESP|sk-ant-api)" .env.example; then
    echo "❌ FAIL: Real keys found in .env.example"
    exit 1
fi

echo "✅ PASS: No API keys found in codebase"
echo "✅ Safe to build and distribute"
```

---

## 📊 Impact Analysis

### **Before Migration (Current Risk):**
| Metric | Value |
|--------|-------|
| Users sharing your Reddit quota | Unlimited |
| Users charging your Claude API | Unlimited |
| Monthly cost exposure | Unlimited |
| Reddit rate limit conflicts | HIGH |
| Terms of Service violation | YES (Reddit) |

### **After Migration (User-Provided Keys):**
| Metric | Value |
|--------|-------|
| Users sharing your Reddit quota | 0 |
| Users charging your Claude API | 0 |
| Monthly cost exposure | $0 |
| Reddit rate limit conflicts | NONE |
| Terms of Service violation | NO |

---

**Document Status:** ✅ Complete - Ready for Implementation
**Priority:** 🔴 **CRITICAL** - Must complete before distributing app
**Next Step:** Begin Phase 1 - Create API Key Management System
