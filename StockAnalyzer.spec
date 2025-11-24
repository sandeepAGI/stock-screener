# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for StockAnalyzer Pro - Programmatic Streamlit Approach

This uses analytics_dashboard.py as direct entry point with programmatic
Streamlit execution (no subprocess launcher needed).
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

# Collect Streamlit data files and metadata
streamlit_datas = collect_data_files('streamlit')
streamlit_metadata = copy_metadata('streamlit')
plotly_datas = collect_data_files('plotly')
altair_datas = collect_data_files('altair')

a = Analysis(
    ['launcher.py'],  # Launcher as entry point
    pathex=[],
    binaries=[],
    datas=[
        # Dashboard script (needed by launcher)
        ('analytics_dashboard.py', '.'),

        # Source code
        ('src', 'src'),
        ('utilities', 'utilities'),

        # Configuration
        ('config', 'config'),

        # Include .env.example as template
        ('.env.example', '.'),

        # Logo if exists
        ('src/data/Logo-Element-Retina.png', 'src/data'),

        # Streamlit dependencies
        *streamlit_datas,
        *streamlit_metadata,
        *plotly_datas,
        *altair_datas,
    ],
    hiddenimports=[
        # Streamlit
        'streamlit',
        'streamlit.runtime',
        'streamlit.runtime.scriptrunner',
        'streamlit.runtime.scriptrunner.magic_funcs',
        'streamlit.runtime.scriptrunner.script_runner',
        'streamlit.runtime.state',
        'streamlit.runtime.caching',
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
