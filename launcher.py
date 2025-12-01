#!/usr/bin/env python3
"""
Launcher for StockAnalyzer Pro - PyInstaller Entry Point

This launches Streamlit programmatically using the correct approach
for frozen PyInstaller apps.
"""

import sys
import os
import webbrowser
import threading
import time
import shutil
from streamlit.web import cli as stcli

def get_user_data_dir():
    """Get the user data directory for the app"""
    if sys.platform == 'darwin':
        return os.path.expanduser('~/Library/Application Support/StockAnalyzer')
    elif sys.platform == 'win32':
        return os.path.join(os.environ.get('APPDATA', ''), 'StockAnalyzer')
    else:
        return os.path.expanduser('~/.stockanalyzer')

def setup_database():
    """
    Initialize database on first run.
    Copies template database if user database doesn't exist.
    """
    if not getattr(sys, 'frozen', False):
        # Not frozen, skip - dev mode uses local database
        return

    user_data_dir = get_user_data_dir()
    user_db_path = os.path.join(user_data_dir, 'stock_data.db')

    # Create user data directory if it doesn't exist
    os.makedirs(user_data_dir, exist_ok=True)

    # If user database doesn't exist, copy template
    if not os.path.exists(user_db_path):
        # Template is bundled in the app
        app_dir = sys._MEIPASS
        template_db_path = os.path.join(app_dir, 'data', 'stock_data_template.db')

        if os.path.exists(template_db_path):
            print(f"First run: Initializing database at {user_db_path}")
            shutil.copy(template_db_path, user_db_path)
            print("Database initialized successfully!")
        else:
            print(f"Warning: Template database not found at {template_db_path}")
    else:
        print(f"Using existing database at {user_db_path}")

def open_browser():
    """Open browser after a short delay to let Streamlit start"""
    time.sleep(3)  # Wait for Streamlit to be ready
    webbrowser.open('http://localhost:8501')

if __name__ == "__main__":
    # Initialize database on first run (frozen apps only)
    setup_database()
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

    # Start browser opening in background thread
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()

    # Run Streamlit
    sys.exit(stcli.main())
