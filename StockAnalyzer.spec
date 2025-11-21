# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for StockAnalyzer Pro (macOS)

This configuration bundles:
- Launcher script
- Streamlit dashboard
- All source code
- Required dependencies
- Database schema (empty database will be created in user's home)

IMPORTANT: Does NOT bundle .env file or API keys
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all Streamlit data files
streamlit_datas = collect_data_files('streamlit')

# Collect all Plotly data files
plotly_datas = collect_data_files('plotly')

# Collect altair data files (used by Streamlit)
altair_datas = collect_data_files('altair')

a = Analysis(
    ['launcher_macos.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Dashboard file
        ('analytics_dashboard.py', '.'),

        # All source code
        ('src', 'src'),

        # Logo file (if exists)
        ('src/data/Logo-Element-Retina.png', 'src/data'),

        # Configuration template (not actual config with keys!)
        ('config.yaml.example', '.') if os.path.exists('config.yaml.example') else None,

        # Streamlit dependencies
        *streamlit_datas,
        *plotly_datas,
        *altair_datas,
    ],
    hiddenimports=[
        # Streamlit and dependencies
        'streamlit',
        'streamlit.runtime',
        'streamlit.runtime.scriptrunner',
        'streamlit.web',
        'streamlit.web.cli',

        # Plotting libraries
        'plotly',
        'plotly.graph_objs',
        'plotly.express',

        # Data processing
        'pandas',
        'numpy',

        # Database
        'sqlite3',

        # APIs
        'anthropic',
        'praw',
        'yfinance',
        'requests',

        # Security
        'keyring',
        'keyring.backends',
        'keyring.backends.macOS',

        # Sentiment analysis
        'textblob',
        'vaderSentiment',
        'vaderSentiment.vaderSentiment',

        # Environment
        'dotenv',
        'python-dotenv',

        # Web browser
        'webbrowser',

        # Additional Streamlit components
        'validators',
        'watchdog',
        'tornado',
        'pyarrow',

        # Altair (used by Streamlit)
        'altair',

        # Our modules
        'src.utils.api_key_manager',
        'src.ui.api_config_ui',
        'src.data.collectors',
        'src.data.sentiment_analyzer',
        'src.data.database',
        'src.data.unified_bulk_processor',
        'src.data.bulk_sentiment_processor',
        'src.calculations.composite',
        'src.calculations.fundamental',
        'src.calculations.quality',
        'src.calculations.growth',
        'src.calculations.sentiment',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude test files
        'pytest',
        'pytest-cov',
        'black',
        'flake8',
        'tests',

        # Exclude development tools
        'IPython',
        'notebook',
        'jupyter',

        # Exclude unnecessary modules
        'matplotlib',  # Not used in this app
        'scipy',       # Not used directly
    ],
    noarchive=False,
    optimize=0,
)

# Filter out None entries from datas
a.datas = [entry for entry in a.datas if entry is not None]

# Remove .env files if they somehow got included
a.datas = [entry for entry in a.datas if not entry[0].endswith('.env')]

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
    console=True,  # Show console for status messages
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
    icon=None,  # Add icon path here if you create one: icon='assets/icon.icns'
    bundle_identifier='com.stockanalyzer.app',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True',
        'CFBundleName': 'StockAnalyzer Pro',
        'CFBundleDisplayName': 'StockAnalyzer Pro',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHumanReadableCopyright': 'Copyright © 2025',
    },
)
