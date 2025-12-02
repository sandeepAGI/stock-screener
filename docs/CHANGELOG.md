# Changelog

All notable changes to StockAnalyzer Pro.

## December 1, 2025 - Electron Migration Phase 2

### Added

- Electron desktop shell (`electron/`)
- Main process with Python backend lifecycle management
- Preload script for secure IPC bridge
- Native macOS menu with keyboard shortcuts
- Splash screen during startup
- App icon placeholder (SVG)
- electron-builder configuration for macOS packaging

### Features

- Automatic Python backend startup/shutdown
- Development mode with hot reload
- Graceful shutdown handling
- External link handling
- Error dialogs for startup issues

---

## December 1, 2025 - Electron Migration Phase 1

### Added

- FastAPI backend for Electron migration (`backend/`)
- REST API endpoints:
  - `GET /api/health` - Health check
  - `GET /api/stocks` - List all stocks
  - `GET /api/stocks/{symbol}` - Stock details with scores
  - `GET /api/rankings` - Composite rankings
  - `GET /api/rankings/sector/{sector}` - Sector rankings
  - `POST /api/data/refresh` - Trigger data refresh
  - `GET /api/data/status` - Collection status
  - `GET /api/data/metrics/summary` - Database stats
  - `POST /api/sentiment/submit` - Submit sentiment batch
  - `GET /api/sentiment/status/{id}` - Batch status
  - `POST /api/calculate` - Run calculations
- WebSocket endpoint for real-time progress updates
- Pydantic models for type-safe API responses
- OpenAPI docs at `/api/docs`

### Architecture

- `backend/main.py` - FastAPI app entry
- `backend/api/` - Route handlers
- `backend/models/` - Pydantic schemas

---

## December 1, 2025 - Codebase Cleanup

### Changed

- Reset `main` branch to stable Streamlit-only version
- Renamed `prod` branch to `dev` for future development
- Removed PyInstaller distribution code (moving to Electron)
- Consolidated documentation to 4 files

### Removed

- `StockAnalyzer.spec`, `launcher.py` (PyInstaller)
- `streamlit_app.py`, `launch_dashboard.py` (legacy dashboards)
- `analytics_dashboard_backup.py`, `analytics_dashboard_original.py`
- Old database backups from git tracking
- Obsolete documentation (19 files)

### Fixed

- `active_batches` UnboundLocalError in Data Management tab

---

## November 2025 - Batch Processing & Dashboard

### Added

- Unified bulk sentiment processing via Anthropic Batch API
- Background batch monitor (`utilities/batch_monitor.py`)
- S&P 500 composition sync with auto-detection of changes
- Individual stock analysis with peer comparison
- Interactive visualizations with hover data

### Fixed

- Yahoo Finance API structure change for news collection
- Reddit false positive filtering (18% reduction)
- Batch tracking schema issues

---

## October 2025 - Visualization Enhancements

### Added

- Histogram with ticker hover data
- Box plot with outlier highlighting (1.5 × IQR)
- Rich tooltips with company names and scores

---

## September 2025 - Core Platform

### Added

- 4-component scoring methodology (Fundamental, Quality, Growth, Sentiment)
- Sector-aware scoring with 11 industry profiles
- Streamlit dashboard with 3-step workflow
- CLI tools for data management
- SQLite database with batch tracking

### Architecture

- `src/calculations/` - Score calculators
- `src/data/` - Data collection and storage
- `utilities/` - CLI tools
- `analytics_dashboard.py` - Main UI
