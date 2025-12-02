# Electron Migration Plan

**Created:** December 1, 2025
**Status:** Planning
**Branch:** dev

---

## Executive Summary

Migrate StockAnalyzer Pro from Streamlit (browser-based) to Electron (native desktop app) for better distribution and user experience.

### Why Electron over Tauri?

| Factor | Electron | Tauri |
|--------|----------|-------|
| AI coding support | More training data, examples | Less common |
| Learning curve | JavaScript only | Requires Rust |
| Maturity | 60% market share, battle-tested | Growing but younger |
| Bundle size | Larger (~270MB with Python) | Smaller (~130MB) |

**Decision:** Start with Electron for faster development, consider Tauri for v2.0 if size becomes an issue.

### Distribution Model

- **Database:** Empty template bundled; user data in `~/Library/Application Support/`
- **API Keys:** User provides their own (first-run setup wizard)
- **Python:** Bundled in app (user doesn't need Python installed)

---

## Current Architecture

```
┌─────────────────────────────────────────┐
│           Streamlit Dashboard           │
│         (analytics_dashboard.py)        │
│              2,949 lines                │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│            Python Backend               │
├─────────────────────────────────────────┤
│  src/calculations/  (6 modules)         │
│  - composite.py, fundamental.py         │
│  - quality.py, growth.py, sentiment.py  │
│  - sector_adjustments.py                │
├─────────────────────────────────────────┤
│  src/data/  (12 modules)                │
│  - database.py, collectors.py           │
│  - bulk_sentiment_processor.py          │
│  - unified_bulk_processor.py            │
│  - sentiment_analyzer.py                │
├─────────────────────────────────────────┤
│  utilities/  (9 CLI tools)              │
│  - smart_refresh.py, batch_monitor.py   │
│  - sync_sp500.py, backup_database.py    │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         SQLite Database                 │
│       (data/stock_data.db)              │
│            ~100 MB                      │
└─────────────────────────────────────────┘
```

---

## Target Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Electron App                              │
├──────────────────────────┬──────────────────────────────────┤
│                          │                                   │
│   React/TypeScript UI    │      Python Backend (FastAPI)    │
│                          │                                   │
│   - Dashboard views      │      - REST API endpoints        │
│   - Charts (Recharts)    │      - WebSocket for progress    │
│   - Forms & inputs       │      - Reuses existing src/      │
│   - State management     │      - SQLite access             │
│                          │                                   │
│   Port: renderer         │      Port: 8000                  │
│                          │                                   │
└──────────────────────────┴──────────────────────────────────┘
                  │                        │
                  │         HTTP/WS        │
                  └────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                    SQLite Database                           │
│              ~/Library/Application Support/                  │
│                  StockAnalyzer/stock_data.db                │
└─────────────────────────────────────────────────────────────┘
```

---

## Migration Phases

### Phase 1: FastAPI Backend (8-12 hours)

**Goal:** Create REST API that exposes existing Python functionality

**Endpoints to create:**

```
GET  /api/health                    - Health check
GET  /api/stocks                    - List all stocks
GET  /api/stocks/{symbol}           - Stock details + scores
GET  /api/rankings                  - Composite rankings
GET  /api/rankings/sector/{sector}  - Sector rankings

POST /api/data/refresh              - Trigger data refresh
GET  /api/data/status               - Collection status
POST /api/sentiment/submit          - Submit batch
GET  /api/sentiment/status/{id}     - Batch status

POST /api/calculate                 - Run calculations
GET  /api/metrics/summary           - Database stats

WS   /ws/progress                   - Real-time progress updates
```

**Files to create:**
```
backend/
├── main.py              # FastAPI app entry
├── api/
│   ├── stocks.py        # Stock endpoints
│   ├── rankings.py      # Ranking endpoints
│   ├── data.py          # Data management endpoints
│   ├── sentiment.py     # Sentiment endpoints
│   └── calculate.py     # Calculation endpoints
├── models/
│   └── schemas.py       # Pydantic models
└── requirements.txt     # FastAPI deps
```

**Key principle:** Reuse existing `src/` modules, just wrap with API.

---

### Phase 2: Electron Shell (4-6 hours)

**Goal:** Create Electron app that launches Python backend + React frontend

**Structure:**
```
electron/
├── main.js              # Electron main process
├── preload.js           # IPC bridge
├── package.json
└── assets/
    └── icon.icns        # App icon
```

**Responsibilities:**
- Start Python backend on app launch
- Open React frontend in BrowserWindow
- Handle app lifecycle (quit, minimize, etc.)
- Package for macOS (.app, .dmg)

---

### Phase 3: React Frontend (12-16 hours)

**Goal:** Recreate Streamlit UI in React/TypeScript

**Structure:**
```
frontend/
├── src/
│   ├── App.tsx
│   ├── components/
│   │   ├── Dashboard/
│   │   ├── Rankings/
│   │   ├── StockAnalysis/
│   │   ├── DataManagement/
│   │   └── common/
│   ├── hooks/
│   │   ├── useStocks.ts
│   │   ├── useRankings.ts
│   │   └── useProgress.ts
│   ├── api/
│   │   └── client.ts    # Axios/fetch wrapper
│   └── types/
│       └── index.ts
├── package.json
└── vite.config.ts
```

**UI Components to build:**

| Streamlit Feature | React Equivalent |
|-------------------|------------------|
| Tabs | React Router or Tabs component |
| st.dataframe | AG Grid or TanStack Table |
| st.plotly_chart | Recharts or Plotly.js |
| st.metric | Custom Card component |
| st.progress | Progress bar component |
| st.selectbox | Select/Dropdown component |
| st.button | Button component |
| st.spinner | Loading spinner |

---

### Phase 4: Integration & Testing (4-6 hours)

**Goal:** Connect all pieces, test end-to-end

**Tasks:**
- Electron launches backend + frontend
- API calls work from React
- WebSocket progress updates
- Database isolation (Application Support)
- Error handling

---

### Phase 5: Packaging & Distribution (4-6 hours)

**Goal:** Create distributable macOS app

**Tools:**
- electron-builder for packaging
- Code signing (optional for initial release)
- DMG creation

**Output:**
- `StockAnalyzer-{version}-mac.dmg`
- Auto-update capability (future)

---

## Time Estimates

| Phase | Task | Hours |
|-------|------|-------|
| 1 | FastAPI Backend | 8-12 |
| 2 | Electron Shell | 4-6 |
| 3 | React Frontend | 12-16 |
| 4 | Integration & Testing | 4-6 |
| 5 | Packaging | 4-6 |
| **Total** | | **32-46 hours** |

---

## Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation
- Existing: SQLite, pandas, numpy

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Recharts** or **Plotly.js** - Charts
- **TanStack Table** - Data tables
- **Tailwind CSS** - Styling

### Desktop
- **Electron** - Desktop wrapper
- **electron-builder** - Packaging

---

## Key Decisions

### 1. Why FastAPI over Flask?
- Async support for long operations
- Automatic OpenAPI docs
- Built-in WebSocket support
- Pydantic validation

### 2. Why Recharts over Plotly?
- Smaller bundle size
- Better React integration
- Sufficient for our charts
- (Alternative: keep Plotly.js if complex charts needed)

### 3. Python Backend vs Node.js?
- **Keep Python** - reuse all existing calculation logic
- No need to rewrite 35 Python modules
- FastAPI is performant enough

### 4. Database Location
- Development: `<project>/data/stock_data.db`
- Production: `~/Library/Application Support/StockAnalyzer/`

---

## API Key Setup (First-Run Wizard)

Users must provide their own API keys. The app will NOT bundle any API keys.

### Required Keys

| Key | Purpose | Where to Get |
|-----|---------|--------------|
| Reddit Client ID | Social sentiment | https://www.reddit.com/prefs/apps |
| Reddit Client Secret | Social sentiment | https://www.reddit.com/prefs/apps |
| Anthropic API Key | LLM sentiment analysis | https://console.anthropic.com |

### First-Run Flow

```
┌─────────────────────────────────────────────────────────────┐
│                 Welcome to StockAnalyzer Pro                │
│                                                             │
│  To analyze stocks, you'll need API keys:                   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Reddit API (for social sentiment)                    │   │
│  │                                                      │   │
│  │ Client ID:     [________________________]            │   │
│  │ Client Secret: [________________________]            │   │
│  │                                                      │   │
│  │ [How to get Reddit API keys →]                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Anthropic API (for AI sentiment analysis)            │   │
│  │                                                      │   │
│  │ API Key:       [________________________]            │   │
│  │                                                      │   │
│  │ [How to get Anthropic API key →]                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│                    [Save & Continue]                        │
└─────────────────────────────────────────────────────────────┘
```

### Secure Storage

- **macOS:** Store in Keychain (via `keytar` npm package)
- **Fallback:** Encrypted file in Application Support
- **Never:** Plain text, bundled in app, or git-committed

---

## Python Bundling

Users do NOT need Python installed. Python is bundled inside the app.

### Bundle Structure

```
StockAnalyzer.app/
├── Contents/
│   ├── MacOS/
│   │   └── StockAnalyzer          # Electron main
│   ├── Resources/
│   │   ├── python/                # Bundled Python (~50MB)
│   │   │   ├── bin/
│   │   │   │   └── python3.11
│   │   │   └── lib/
│   │   │       └── python3.11/
│   │   │           └── site-packages/  # Pre-installed deps
│   │   ├── backend/               # Your Python code
│   │   │   ├── main.py            # FastAPI entry
│   │   │   └── src/               # Existing modules
│   │   ├── frontend/              # React build
│   │   └── data/
│   │       └── stock_data_template.db  # Empty schema
│   └── Frameworks/                # Electron runtime
```

### How Python is Bundled

**Option A: python-build-standalone**
- Pre-built portable Python distributions
- Download from: https://github.com/indygreg/python-build-standalone
- Just extract and include in Resources/

**Option B: PyInstaller for backend only**
- Bundle Python + deps as single folder
- Electron spawns this

**Option C: Nuitka**
- Compile Python to C, then to binary
- Smaller but more complex

**Recommendation:** Option A (simplest, well-tested)

### App Startup Sequence

```
1. User double-clicks StockAnalyzer.app
2. Electron main process starts
3. Check for first-run (API keys setup)
4. Spawn: Resources/python/bin/python3 Resources/backend/main.py
5. Wait for FastAPI to be ready (health check)
6. Open BrowserWindow pointing to React frontend
7. Frontend connects to localhost:8000
```

### Shutdown Sequence

```
1. User closes window or quits app
2. Electron catches 'before-quit' event
3. Send SIGTERM to Python process
4. Wait up to 5 seconds for graceful shutdown
5. Force kill if needed
6. Exit Electron
```

---

## Migration Strategy

### Incremental Approach

1. **Week 1:** FastAPI backend (Phase 1)
   - Test with curl/Postman
   - Existing Streamlit still works

2. **Week 2:** Electron + basic React (Phase 2-3 start)
   - Simple dashboard view
   - Rankings table

3. **Week 3:** Complete React UI (Phase 3 finish)
   - All views migrated
   - Charts working

4. **Week 4:** Polish & Package (Phase 4-5)
   - Testing
   - DMG creation

### Parallel Development
- Streamlit remains functional on `main`
- Electron development on `dev`
- Merge to `main` when stable

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Python/Electron IPC complexity | Use HTTP API, not IPC |
| Chart library learning curve | Start with simple charts |
| Backend process management | Use child_process with proper cleanup |
| Large bundle size | Exclude unused deps, use tree shaking |

---

## Success Criteria

1. **Functionality:** All Streamlit features work in Electron
2. **Performance:** App launches in <5 seconds
3. **Size:** DMG < 300MB
4. **Stability:** No crashes during normal use
5. **UX:** Native app feel (menu bar, dock icon, etc.)

---

## Next Steps

1. [ ] Review and approve this plan
2. [ ] Set up FastAPI project structure
3. [ ] Create first API endpoint (GET /api/stocks)
4. [ ] Test with existing database
