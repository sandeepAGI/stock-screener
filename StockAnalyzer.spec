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

        # Template database for first-run initialization
        ('data/stock_data_template.db', 'data'),

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
        'peewee',
        'playhouse',
        'playhouse.sqlite_ext',

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
        'lxml',
        'lxml.etree',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude test files
        'pytest',
        'tests',
        'unittest',

        # Exclude dev tools
        'IPython',
        'notebook',
        'jupyter',
        'sphinx',
        'docutils',

        # Exclude ML/DL frameworks (NOT USED)
        'tensorflow',
        'torch',
        'torchvision',
        'torchtext',
        'torchaudio',
        'keras',
        'theano',

        # Exclude CV/Image processing (NOT USED)
        'cv2',
        'opencv',
        'PIL.ImageQt',
        'skimage',

        # Exclude ML libraries (NOT USED)
        'sklearn',
        'scikit-learn',
        'scikit-image',
        'xgboost',
        'lightgbm',
        'catboost',

        # Exclude NLP (NOT USED - we only use textblob/vader)
        'spacy',
        'nltk',
        'transformers',
        'tokenizers',
        'gensim',

        # Exclude ONNX (NOT USED)
        'onnx',
        'onnxruntime',

        # Exclude Qt (NOT USED)
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'qtpy',

        # Exclude visualization tools (NOT USED - we use plotly)
        'matplotlib',
        'scipy',
        'bokeh',
        'panel',
        'holoviews',
        'seaborn',
        'dash',

        # Exclude geospatial (NOT USED)
        'pyogrio',
        'geopandas',
        'fiona',
        'shapely',
        'gdal',
        'osgeo',
        'pyproj',
        'cartopy',

        # Exclude AWS/Cloud (NOT USED)
        'boto',
        'boto3',
        'botocore',
        's3transfer',
        'awscli',

        # Exclude database drivers (NOT USED - we only use sqlite3)
        'psycopg2',
        'pymongo',
        'redis',
        'sqlalchemy',

        # Exclude web scraping (NOT USED - we use yfinance/praw APIs)
        'selenium',
        'scrapy',
        'beautifulsoup4',
        # Note: lxml is needed for S&P 500 sync (pd.read_html)

        # Exclude unnecessary data formats
        'xlrd',
        'xlwt',
        'openpyxl',
        'h5py',
        'tables',

        # Exclude astropy (NOT USED)
        'astropy',
        'astropy_iers_data',

        # Exclude GUI frameworks (NOT USED)
        'tkinter',
        'wx',
        'kivy',

        # Note: Can't exclude distutils, setuptools (PyInstaller needs them)

        # Exclude typing extensions we don't need
        'mypy',
        'pylint',
        'black',
        'flake8',
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
        'CFBundleVersion': '0.2.1',
        'CFBundleShortVersionString': '0.2.1',
        'NSHumanReadableCopyright': 'Copyright © 2025',
    },
)
