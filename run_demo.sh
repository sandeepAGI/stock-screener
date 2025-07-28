#!/bin/bash
# Demo Dashboard Launcher
# Quick script to launch the analytics dashboard for tomorrow's demo

echo "🚀 Launching Stock Outlier Analytics Dashboard..."
echo "📊 Using data from: data/stock_data.db"

# Activate virtual environment
source venv/bin/activate

# Launch dashboard
echo "🌐 Starting dashboard on http://localhost:8503"
echo "📋 Press Ctrl+C to stop the dashboard"
echo ""

streamlit run analytics_dashboard.py --server.port=8503

echo "✅ Dashboard stopped"