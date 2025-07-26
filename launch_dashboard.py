#!/usr/bin/env python3
"""
StockAnalyzer Pro Dashboard Launcher
Initializes database schema and launches the Streamlit dashboard
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import subprocess
from datetime import datetime, date

def initialize_database():
    """Initialize empty database with proper schema for user-controlled data management"""
    print("🔧 Initializing Database Schema...")
    
    try:
        from src.data.database import DatabaseManager
        
        # Initialize database manager
        db = DatabaseManager()
        
        if not db.connect():
            print("❌ Failed to connect to database")
            return False
        
        # Create tables if they don't exist
        db.create_tables()
        print("✅ Database schema initialized")
        
        # Check if any stocks exist
        stocks = db.get_all_stocks()
        if stocks:
            print(f"📊 Found {len(stocks)} existing stocks in database")
        else:
            print("📝 Empty database - use Data Management section to add stocks")
        
        db.close()
        print("✅ Database initialization completed")
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {str(e)}")
        return False

def launch_dashboard():
    """Launch the Streamlit dashboard"""
    print("\n🚀 Launching StockAnalyzer Pro Dashboard...")
    print("=" * 50)
    print("Dashboard will open in your default web browser")
    print("URL: http://localhost:8501")
    print("Press Ctrl+C to stop the dashboard")
    print("=" * 50)
    
    try:
        # Launch Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n✅ Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Failed to launch dashboard: {str(e)}")

def main():
    """Main launcher function"""
    print("🎯 StockAnalyzer Pro Dashboard Launcher")
    print("=" * 50)
    
    # Initialize database schema
    if initialize_database():
        print("\n✅ Database ready!")
        
        # Ask user if they want to launch
        try:
            response = input("\nLaunch dashboard now? (y/n): ").lower().strip()
            if response in ['y', 'yes', '']:
                launch_dashboard()
            else:
                print("Dashboard ready to launch manually with:")
                print("streamlit run streamlit_app.py")
        except KeyboardInterrupt:
            print("\n✅ Launcher stopped by user")
    else:
        print("❌ Database initialization failed. Cannot launch dashboard.")
        sys.exit(1)

if __name__ == "__main__":
    main()