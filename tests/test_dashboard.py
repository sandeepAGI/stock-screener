#!/usr/bin/env python3
"""
Test Streamlit Dashboard Dependencies
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_dashboard_dependencies():
    """Test all dashboard dependencies"""
    print("🧪 Testing Streamlit Dashboard Dependencies...")
    
    try:
        # Test core imports
        import streamlit as st
        import pandas as pd
        import numpy as np
        import plotly.express as px
        import plotly.graph_objects as go
        print("✅ Streamlit and visualization libraries imported")
        
        # Test our calculation modules
        from src.calculations.fundamental import FundamentalCalculator
        from src.calculations.quality import QualityCalculator
        from src.calculations.growth import GrowthCalculator
        from src.calculations.sentiment import SentimentCalculator
        from src.calculations.composite import CompositeCalculator
        print("✅ All calculation modules imported")
        
        # Test database and utilities
        from src.data.database import DatabaseManager
        from src.utils.helpers import load_config
        print("✅ Database and utility modules imported")
        
        # Test configuration loading
        config = load_config()
        print("✅ Configuration loaded successfully")
        
        # Test calculator instantiation
        calculators = {
            'fundamental': FundamentalCalculator(),
            'quality': QualityCalculator(),
            'growth': GrowthCalculator(),
            'sentiment': SentimentCalculator(),
            'composite': CompositeCalculator()
        }
        print("✅ All calculators instantiated successfully")
        
        # Test sample data creation
        sample_data = [
            {
                'symbol': 'TEST',
                'company': 'Test Company',
                'sector': 'Technology',
                'composite_score': 75.0,
                'overall_data_quality': 0.85
            }
        ]
        df = pd.DataFrame(sample_data)
        print("✅ Sample data creation working")
        
        # Test plotly chart creation
        fig = px.bar(df, x='symbol', y='composite_score', title='Test Chart')
        print("✅ Plotly chart creation working")
        
        print("\n🎉 ALL DASHBOARD DEPENDENCIES WORKING!")
        print("Dashboard is ready to run.")
        print("\nTo launch the dashboard, run:")
        print("streamlit run streamlit_app.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Dashboard dependency test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_dashboard_dependencies()
    sys.exit(0 if success else 1)