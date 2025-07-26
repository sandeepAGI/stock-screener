#!/usr/bin/env python3
"""
Launch Dashboard with Sample Data
Prepares sample data and launches the Streamlit dashboard
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import subprocess
from datetime import datetime, date

def prepare_sample_data():
    """Prepare sample data for dashboard demonstration"""
    print("🔧 Preparing Sample Data for Dashboard...")
    
    try:
        from src.data.database import DatabaseManager
        from src.calculations.composite import CompositeCalculator
        
        # Initialize database
        db = DatabaseManager()
        
        # Use a demo database
        demo_db_path = "demo_stock_data.db"
        if os.path.exists(demo_db_path):
            os.remove(demo_db_path)
        
        db.db_path = demo_db_path
        
        if not db.connect():
            print("❌ Failed to create demo database")
            return False
        
        db.create_tables()
        print("✅ Demo database created")
        
        # Add sample stocks
        sample_stocks = [
            ("AAPL", "Apple Inc.", "Technology", "Technology Hardware"),
            ("MSFT", "Microsoft Corporation", "Technology", "Software"),
            ("GOOGL", "Alphabet Inc.", "Communication Services", "Internet Content & Information"),
            ("TSLA", "Tesla Inc.", "Consumer Discretionary", "Automobiles"),
            ("JNJ", "Johnson & Johnson", "Healthcare", "Pharmaceuticals"),
            ("JPM", "JPMorgan Chase & Co.", "Financials", "Banks"),
            ("NVDA", "NVIDIA Corporation", "Technology", "Semiconductors"),
            ("UNH", "UnitedHealth Group", "Healthcare", "Health Care Plans"),
            ("V", "Visa Inc.", "Financials", "Data Processing & Services"),
            ("WMT", "Walmart Inc.", "Consumer Staples", "Food & Staples Retailing")
        ]
        
        for symbol, name, sector, industry in sample_stocks:
            db.insert_stock(symbol, name, sector, industry, None, "NYSE/NASDAQ")
        
        print(f"✅ Added {len(sample_stocks)} sample stocks")
        
        # Add mock fundamental data for demonstration
        mock_fundamentals = {
            'pe_ratio': 25.0,
            'ev_to_ebitda': 18.0,
            'peg_ratio': 1.5,
            'free_cash_flow': 80000000000,
            'market_cap': 3000000000000,
            'total_revenue': 400000000000,
            'net_income': 100000000000,
            'total_assets': 350000000000,
            'total_debt': 120000000000,
            'shareholders_equity': 60000000000,
            'return_on_equity': 0.18,
            'debt_to_equity': 0.3,
            'current_ratio': 1.8,
            'revenue_growth': 0.08,
            'earnings_growth': 0.12,
            'data_source': 'demo_data'
        }
        
        # Add fundamental data for first few stocks
        for symbol, _, _, _ in sample_stocks[:5]:
            # Vary the data slightly for each stock
            varied_fundamentals = mock_fundamentals.copy()
            varied_fundamentals['pe_ratio'] *= (0.8 + hash(symbol) % 40 / 100)  # Vary PE ratio
            varied_fundamentals['revenue_growth'] *= (0.5 + hash(symbol) % 100 / 100)  # Vary growth
            
            db.insert_fundamental_data(symbol, varied_fundamentals)
        
        print("✅ Added mock fundamental data")
        
        db.close()
        print("✅ Sample data preparation completed")
        return True
        
    except Exception as e:
        print(f"❌ Sample data preparation failed: {str(e)}")
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
    
    # Prepare sample data
    if prepare_sample_data():
        print("\n✅ Sample data ready!")
        
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
        print("❌ Sample data preparation failed. Cannot launch dashboard.")
        sys.exit(1)

if __name__ == "__main__":
    main()