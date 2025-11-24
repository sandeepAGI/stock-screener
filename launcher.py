#!/usr/bin/env python3
"""
Launcher for StockAnalyzer Pro - PyInstaller Entry Point

This launches Streamlit programmatically using the correct approach
for frozen PyInstaller apps.
"""

import sys
import os
from streamlit.web import cli as stcli

if __name__ == "__main__":
    # Get the directory where this script is located
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        app_dir = sys._MEIPASS
        script_path = os.path.join(app_dir, 'analytics_dashboard.py')
    else:
        # Running in development
        script_path = os.path.join(os.path.dirname(__file__), 'analytics_dashboard.py')

    # Set up Streamlit arguments
    sys.argv = [
        "streamlit",
        "run",
        script_path,
        "--server.headless=true",
        "--server.port=8501",
        "--server.address=localhost",
        "--browser.serverAddress=localhost",
        "--browser.gatherUsageStats=false",
        "--server.enableXsrfProtection=false",  # Disable XSRF for local use
        "--server.enableCORS=true",
        "--global.developmentMode=false",
    ]

    # Run Streamlit
    sys.exit(stcli.main())
