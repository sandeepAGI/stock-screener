#!/bin/bash
# StockAnalyzer Dashboard Launcher
# Always uses the correct virtual environment

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🚀 Launching Stock Outlier Analytics Dashboard..."
echo "📊 Using data from: data/stock_data.db"

# Activate virtual environment (ensures correct Python/packages)
source venv/bin/activate

# Launch dashboard on default port
echo "🌐 Starting dashboard on http://localhost:8501"
echo "📋 Press Ctrl+C to stop the dashboard"
echo ""

streamlit run analytics_dashboard.py

echo "✅ Dashboard stopped"