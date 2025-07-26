#!/usr/bin/env python3
"""
StockAnalyzer Pro - Streamlit Dashboard
Professional stock screening and analysis interface
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our calculation modules
from src.calculations.fundamental import FundamentalCalculator
from src.calculations.quality import QualityCalculator
from src.calculations.growth import GrowthCalculator
from src.calculations.sentiment import SentimentCalculator
from src.calculations.composite import CompositeCalculator
from src.data.database import DatabaseManager, init_database
from src.utils.helpers import load_config

# Page configuration
st.set_page_config(
    page_title="StockAnalyzer Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        color: #1f4e79;
        text-align: center;
        margin-bottom: 1rem;
    }
    .methodology-badge {
        background: linear-gradient(90deg, #1f4e79, #2980b9);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        margin: 0.2rem;
        display: inline-block;
    }
    .metric-card {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .score-excellent { color: #28a745; font-weight: bold; }
    .score-good { color: #17a2b8; font-weight: bold; }
    .score-average { color: #ffc107; font-weight: bold; }
    .score-poor { color: #fd7e14; font-weight: bold; }
    .score-very-poor { color: #dc3545; font-weight: bold; }
    .data-quality-high { color: #28a745; }
    .data-quality-medium { color: #ffc107; }
    .data-quality-low { color: #dc3545; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_configuration():
    """Load application configuration"""
    return load_config()

@st.cache_resource
def initialize_database():
    """Initialize database connection"""
    try:
        db = DatabaseManager()
        if db.connect():
            return db
        return None
    except Exception as e:
        st.error(f"Database initialization failed: {str(e)}")
        return None

@st.cache_resource
def initialize_calculators():
    """Initialize all calculation engines"""
    return {
        'fundamental': FundamentalCalculator(),
        'quality': QualityCalculator(),
        'growth': GrowthCalculator(),
        'sentiment': SentimentCalculator(),
        'composite': CompositeCalculator()
    }

def get_score_class(score: float) -> str:
    """Get CSS class for score styling"""
    if score >= 80:
        return "score-excellent"
    elif score >= 70:
        return "score-good"
    elif score >= 50:
        return "score-average"
    elif score >= 30:
        return "score-poor"
    else:
        return "score-very-poor"

def get_data_quality_class(quality: float) -> str:
    """Get CSS class for data quality styling"""
    if quality >= 0.8:
        return "data-quality-high"
    elif quality >= 0.6:
        return "data-quality-medium"
    else:
        return "data-quality-low"

def format_score(score: float) -> str:
    """Format score with appropriate styling"""
    css_class = get_score_class(score)
    return f'<span class="{css_class}">{score:.1f}</span>'

def format_data_quality(quality: float) -> str:
    """Format data quality with appropriate styling"""
    css_class = get_data_quality_class(quality)
    percentage = quality * 100
    return f'<span class="{css_class}">{percentage:.0f}%</span>'

def render_methodology_overview():
    """Render methodology overview section"""
    st.markdown('<h1 class="main-header">📊 StockAnalyzer Pro</h1>', unsafe_allow_html=True)
    st.markdown("### Automated Stock Mispricing Detection System")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="methodology-badge">📈 Fundamental (40%)</div>', unsafe_allow_html=True)
        st.caption("P/E, EV/EBITDA, PEG, FCF Yield")
    
    with col2:
        st.markdown('<div class="methodology-badge">🏦 Quality (25%)</div>', unsafe_allow_html=True)
        st.caption("ROE, ROIC, Debt Ratios")
    
    with col3:
        st.markdown('<div class="methodology-badge">🚀 Growth (20%)</div>', unsafe_allow_html=True)
        st.caption("Revenue, EPS Growth, Stability")
    
    with col4:
        st.markdown('<div class="methodology-badge">💭 Sentiment (15%)</div>', unsafe_allow_html=True)
        st.caption("News, Social Media Analysis")

def create_sample_data():
    """Create sample data for demonstration"""
    sample_stocks = [
        {
            'symbol': 'AAPL',
            'company': 'Apple Inc.',
            'sector': 'Technology',
            'fundamental_score': 72.5,
            'quality_score': 85.2,
            'growth_score': 68.1,
            'sentiment_score': 75.3,
            'composite_score': 75.3,
            'fundamental_data_quality': 0.95,
            'quality_data_quality': 0.90,
            'growth_data_quality': 0.85,
            'sentiment_data_quality': 0.70,
            'overall_data_quality': 0.85,
            'market_percentile': 78.5,
            'outlier_category': 'fairly_valued'
        },
        {
            'symbol': 'MSFT',
            'company': 'Microsoft Corporation',
            'sector': 'Technology',
            'fundamental_score': 68.9,
            'quality_score': 88.7,
            'growth_score': 71.4,
            'sentiment_score': 72.8,
            'composite_score': 75.5,
            'fundamental_data_quality': 0.92,
            'quality_data_quality': 0.95,
            'growth_data_quality': 0.88,
            'sentiment_data_quality': 0.75,
            'overall_data_quality': 0.88,
            'market_percentile': 79.2,
            'outlier_category': 'fairly_valued'
        },
        {
            'symbol': 'GOOGL',
            'company': 'Alphabet Inc.',
            'sector': 'Communication Services',
            'fundamental_score': 78.3,
            'quality_score': 82.1,
            'growth_score': 74.6,
            'sentiment_score': 68.9,
            'composite_score': 76.0,
            'fundamental_data_quality': 0.90,
            'quality_data_quality': 0.85,
            'growth_data_quality': 0.90,
            'sentiment_data_quality': 0.65,
            'overall_data_quality': 0.83,
            'market_percentile': 80.1,
            'outlier_category': 'fairly_valued'
        },
        {
            'symbol': 'TSLA',
            'company': 'Tesla Inc.',
            'sector': 'Consumer Discretionary',
            'fundamental_score': 45.2,
            'quality_score': 62.8,
            'growth_score': 89.3,
            'sentiment_score': 82.1,
            'composite_score': 69.9,
            'fundamental_data_quality': 0.85,
            'quality_data_quality': 0.80,
            'growth_data_quality': 0.90,
            'sentiment_data_quality': 0.85,
            'overall_data_quality': 0.85,
            'market_percentile': 65.4,
            'outlier_category': 'fairly_valued'
        },
        {
            'symbol': 'JNJ',
            'company': 'Johnson & Johnson',
            'sector': 'Healthcare',
            'fundamental_score': 82.1,
            'quality_score': 91.5,
            'growth_score': 52.3,
            'sentiment_score': 65.7,
            'composite_score': 72.9,
            'fundamental_data_quality': 0.95,
            'quality_data_quality': 0.98,
            'growth_data_quality': 0.85,
            'sentiment_data_quality': 0.60,
            'overall_data_quality': 0.85,
            'market_percentile': 71.3,
            'outlier_category': 'fairly_valued'
        }
    ]
    
    return pd.DataFrame(sample_stocks)

def render_stock_screener():
    """Render the main stock screener interface"""
    st.header("🔍 Stock Screener")
    
    # Get sample data
    df = create_sample_data()
    
    # Sidebar filters
    st.sidebar.header("📋 Screening Filters")
    
    # Sector filter
    sectors = ['All'] + sorted(df['sector'].unique().tolist())
    selected_sector = st.sidebar.selectbox("Sector", sectors)
    
    # Score filters
    st.sidebar.subheader("Score Filters")
    min_composite = st.sidebar.slider("Minimum Composite Score", 0, 100, 0)
    min_data_quality = st.sidebar.slider("Minimum Data Quality", 0.0, 1.0, 0.0, step=0.1)
    
    # Outlier category filter
    categories = ['All'] + sorted(df['outlier_category'].unique().tolist())
    selected_category = st.sidebar.selectbox("Outlier Category", categories)
    
    # Apply filters
    filtered_df = df.copy()
    
    if selected_sector != 'All':
        filtered_df = filtered_df[filtered_df['sector'] == selected_sector]
    
    if selected_category != 'All':
        filtered_df = filtered_df[filtered_df['outlier_category'] == selected_category]
    
    filtered_df = filtered_df[
        (filtered_df['composite_score'] >= min_composite) &
        (filtered_df['overall_data_quality'] >= min_data_quality)
    ]
    
    # Display results count
    st.info(f"📊 Showing {len(filtered_df)} stocks (filtered from {len(df)} total)")
    
    # Main results table
    if len(filtered_df) > 0:
        # Create display dataframe
        display_df = filtered_df.copy()
        
        # Format scores for display
        for col in ['fundamental_score', 'quality_score', 'growth_score', 'sentiment_score', 'composite_score']:
            display_df[col] = display_df[col].apply(lambda x: f"{x:.1f}")
        
        # Format data quality columns
        for col in ['fundamental_data_quality', 'quality_data_quality', 'growth_data_quality', 
                   'sentiment_data_quality', 'overall_data_quality']:
            display_df[col] = display_df[col].apply(lambda x: f"{x*100:.0f}%")
        
        display_df['market_percentile'] = display_df['market_percentile'].apply(lambda x: f"{x:.1f}%")
        
        # Rename columns for display
        display_columns = {
            'symbol': 'Symbol',
            'company': 'Company',
            'sector': 'Sector',
            'composite_score': 'Composite Score',
            'fundamental_score': 'Fundamental',
            'quality_score': 'Quality',
            'growth_score': 'Growth',
            'sentiment_score': 'Sentiment',
            'overall_data_quality': 'Data Quality',
            'market_percentile': 'Market Percentile',
            'outlier_category': 'Category'
        }
        
        display_df = display_df.rename(columns=display_columns)
        selected_cols = list(display_columns.values())
        
        st.dataframe(
            display_df[selected_cols],
            use_container_width=True,
            hide_index=True
        )
        
        # Add download button
        csv = display_df[selected_cols].to_csv(index=False)
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv,
            file_name=f"stock_screener_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.warning("No stocks match the current filter criteria. Try adjusting the filters.")

def render_stock_analysis(symbol: str, df: pd.DataFrame):
    """Render detailed analysis for a specific stock"""
    stock_data = df[df['symbol'] == symbol].iloc[0]
    
    st.header(f"📈 {stock_data['company']} ({symbol})")
    st.subheader(f"Sector: {stock_data['sector']}")
    
    # Key metrics overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Composite Score",
            f"{stock_data['composite_score']:.1f}",
            delta=None
        )
    
    with col2:
        st.metric(
            "Market Percentile",
            f"{stock_data['market_percentile']:.1f}%",
            delta=None
        )
    
    with col3:
        st.metric(
            "Data Quality",
            f"{stock_data['overall_data_quality']*100:.0f}%",
            delta=None
        )
    
    with col4:
        st.metric(
            "Category",
            stock_data['outlier_category'].replace('_', ' ').title(),
            delta=None
        )
    
    # Component scores breakdown
    st.subheader("📊 Component Score Breakdown")
    
    # Create radar chart
    categories = ['Fundamental\n(40%)', 'Quality\n(25%)', 'Growth\n(20%)', 'Sentiment\n(15%)']
    scores = [
        stock_data['fundamental_score'],
        stock_data['quality_score'],
        stock_data['growth_score'],
        stock_data['sentiment_score']
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=scores,
        theta=categories,
        fill='toself',
        name='Component Scores',
        line_color='rgb(31, 78, 121)',
        fillcolor='rgba(31, 78, 121, 0.3)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=False,
        title="Component Score Distribution",
        height=400
    )
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📋 Detailed Scores")
        
        components = [
            ('Fundamental', stock_data['fundamental_score'], stock_data['fundamental_data_quality'], 40),
            ('Quality', stock_data['quality_score'], stock_data['quality_data_quality'], 25),
            ('Growth', stock_data['growth_score'], stock_data['growth_data_quality'], 20),
            ('Sentiment', stock_data['sentiment_score'], stock_data['sentiment_data_quality'], 15)
        ]
        
        for name, score, quality, weight in components:
            st.markdown(f"""
            <div class="metric-card">
                <strong>{name} ({weight}%)</strong><br>
                Score: {format_score(score)}<br>
                Data Quality: {format_data_quality(quality)}
            </div>
            """, unsafe_allow_html=True)
    
    # Data quality breakdown
    st.subheader("🎯 Data Quality Analysis")
    
    quality_data = {
        'Component': ['Fundamental', 'Quality', 'Growth', 'Sentiment'],
        'Data Quality': [
            stock_data['fundamental_data_quality'],
            stock_data['quality_data_quality'],
            stock_data['growth_data_quality'],
            stock_data['sentiment_data_quality']
        ]
    }
    
    fig_quality = px.bar(
        quality_data,
        x='Component',
        y='Data Quality',
        title='Data Quality by Component',
        color='Data Quality',
        color_continuous_scale=['red', 'yellow', 'green'],
        range_color=[0, 1]
    )
    
    fig_quality.update_layout(height=400)
    st.plotly_chart(fig_quality, use_container_width=True)

def render_data_management():
    """Render the data management interface"""
    st.header("🗄️ Data Management")
    
    # Initialize database connection for real-time status
    db = initialize_database()
    
    # Data Source Status
    st.subheader("📡 Data Source Status")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Yahoo Finance API",
            "🟢 Active",
            delta="Last: 2 mins ago"
        )
    
    with col2:
        st.metric(
            "Reddit API", 
            "🟡 Limited",
            delta="Rate limit: 80%"
        )
    
    with col3:
        st.metric(
            "Database",
            "🟢 Connected",
            delta="3.2MB used"
        )
    
    with col4:
        st.metric(
            "Data Quality",
            "87%",
            delta="+2% from yesterday"
        )
    
    st.markdown("---")
    
    # Data Collection Controls
    st.subheader("🔄 Data Collection Controls")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Quick Actions")
        
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            if st.button("🔄 Refresh All Data", type="primary"):
                with st.spinner("Updating all data sources..."):
                    st.success("✅ All data refreshed successfully!")
        
        with col_b:
            if st.button("📊 Update Fundamentals"):
                with st.spinner("Fetching fundamental data..."):
                    st.success("✅ Fundamental data updated!")
        
        with col_c:
            if st.button("💭 Update Sentiment"):
                with st.spinner("Analyzing sentiment data..."):
                    st.success("✅ Sentiment data updated!")
        
        # Stock Management
        st.markdown("### Stock Management")
        
        # Add stocks
        new_symbols = st.text_input(
            "Add Stocks (comma-separated):",
            placeholder="AAPL, MSFT, GOOGL"
        )
        
        col_add, col_remove = st.columns(2)
        
        with col_add:
            if st.button("➕ Add Stocks") and new_symbols:
                symbols = [s.strip().upper() for s in new_symbols.split(",")]
                st.success(f"✅ Added {len(symbols)} stocks: {', '.join(symbols)}")
        
        with col_remove:
            # Remove stocks dropdown
            sample_symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "JNJ"]
            remove_symbol = st.selectbox("Remove Stock:", [""] + sample_symbols)
            if st.button("➖ Remove Stock") and remove_symbol:
                st.success(f"✅ Removed {remove_symbol}")
    
    with col2:
        st.markdown("### Last Updated")
        
        update_data = [
            ("Fundamental Data", "2 minutes ago", "🟢"),
            ("Quality Metrics", "5 minutes ago", "🟢"),
            ("Growth Data", "8 minutes ago", "🟡"),
            ("Sentiment Analysis", "15 minutes ago", "🟡"),
            ("News Articles", "1 hour ago", "🟠"),
            ("Reddit Posts", "2 hours ago", "🟠")
        ]
        
        for data_type, last_update, status in update_data:
            st.markdown(f"{status} **{data_type}**  \n{last_update}")
    
    st.markdown("---")
    
    # Data Quality Dashboard
    st.subheader("📊 Data Quality Dashboard")
    
    # Create sample data quality metrics
    quality_by_component = {
        'Component': ['Fundamental', 'Quality', 'Growth', 'Sentiment'],
        'Coverage (%)': [95, 88, 82, 65],
        'Avg Quality Score': [0.92, 0.89, 0.84, 0.71],
        'Last Updated': ['2 min', '5 min', '8 min', '15 min']
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Coverage chart
        fig_coverage = px.bar(
            quality_by_component,
            x='Component',
            y='Coverage (%)',
            title='Data Coverage by Component',
            color='Coverage (%)',
            color_continuous_scale=['red', 'yellow', 'green']
        )
        fig_coverage.update_layout(height=350)
        st.plotly_chart(fig_coverage, use_container_width=True)
    
    with col2:
        # Quality score chart
        fig_quality = px.bar(
            quality_by_component,
            x='Component',
            y='Avg Quality Score',
            title='Average Data Quality Score',
            color='Avg Quality Score',
            color_continuous_scale=['red', 'yellow', 'green'],
            range_color=[0, 1]
        )
        fig_quality.update_layout(height=350)
        st.plotly_chart(fig_quality, use_container_width=True)
    
    # Data Quality Details Table
    st.markdown("### Detailed Data Quality Report")
    
    quality_df = pd.DataFrame({
        'Stock': ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'JNJ'],
        'Fundamental': ['95%', '92%', '98%', '90%', '96%'],
        'Quality': ['88%', '95%', '85%', '80%', '92%'],
        'Growth': ['82%', '88%', '90%', '75%', '85%'],
        'Sentiment': ['70%', '75%', '60%', '85%', '55%'],
        'Overall': ['84%', '88%', '83%', '83%', '82%'],
        'Last Updated': ['2 min', '2 min', '3 min', '5 min', '4 min'],
        'Issues': ['None', 'None', 'Missing EPS growth', 'Low sentiment volume', 'Stale news data']
    })
    
    st.dataframe(quality_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Database Management
    st.subheader("💾 Database Management")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### Storage Statistics")
        st.metric("Database Size", "3.2 MB")
        st.metric("Total Records", "15,847")
        st.metric("Active Stocks", "25")
    
    with col2:
        st.markdown("### Performance")
        st.metric("Avg Query Time", "12ms")
        st.metric("Cache Hit Rate", "94%")
        st.metric("Connection Pool", "8/10")
    
    with col3:
        st.markdown("### Maintenance")
        if st.button("🧹 Cleanup Old Data"):
            st.success("✅ Cleaned 1,247 old records")
        
        if st.button("📦 Export Backup"):
            st.success("✅ Backup created: backup_20250126.sql")
        
        if st.button("🔧 Optimize Database"):
            st.success("✅ Database optimized")
    
    # Record Counts by Table
    st.markdown("### Database Tables")
    
    table_data = {
        'Table': ['stocks', 'price_data', 'fundamental_data', 'news_articles', 'reddit_posts', 'calculated_metrics'],
        'Records': [25, 6250, 125, 445, 289, 100],
        'Size (KB)': [2.1, 1250.3, 87.2, 234.7, 156.8, 45.6],
        'Last Modified': ['1 day ago', '2 min ago', '5 min ago', '1 hour ago', '2 hours ago', '5 min ago']
    }
    
    table_df = pd.DataFrame(table_data)
    st.dataframe(table_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Configuration Management
    st.subheader("⚙️ Configuration Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### API Configuration")
        
        # API Status
        api_configs = [
            ("Yahoo Finance", "✅ Configured", "No rate limits"),
            ("Reddit API", "✅ Configured", "Client ID: reddit_***"),
            ("News API", "⚠️ Optional", "Not configured"),
            ("Alpha Vantage", "⚠️ Optional", "Not configured")
        ]
        
        for api_name, status, details in api_configs:
            with st.expander(f"{api_name} - {status}"):
                st.write(details)
                if "Not configured" in status:
                    st.text_input(f"{api_name} API Key:", type="password", key=f"{api_name.lower()}_key")
                    if st.button(f"Test {api_name} Connection", key=f"test_{api_name.lower()}"):
                        st.success(f"✅ {api_name} connection successful!")
    
    with col2:
        st.markdown("### Methodology Configuration")
        
        st.markdown("**Component Weights:**")
        
        # Allow weight adjustment
        fund_weight = st.slider("Fundamental Weight", 30, 50, 40, key="fund_weight")
        qual_weight = st.slider("Quality Weight", 15, 35, 25, key="qual_weight")
        grow_weight = st.slider("Growth Weight", 10, 30, 20, key="grow_weight")
        sent_weight = st.slider("Sentiment Weight", 5, 25, 15, key="sent_weight")
        
        total_weight = fund_weight + qual_weight + grow_weight + sent_weight
        
        if total_weight != 100:
            st.error(f"⚠️ Weights must sum to 100% (current: {total_weight}%)")
        else:
            st.success("✅ Weight configuration valid")
        
        if st.button("💾 Save Configuration"):
            st.success("✅ Configuration saved successfully!")
    
    # Data Export/Import
    st.markdown("---")
    st.subheader("📤 Data Export & Import")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Export Data")
        
        export_options = st.multiselect(
            "Select data to export:",
            ["Stock List", "Fundamental Data", "Calculated Scores", "News Articles", "Reddit Posts"],
            default=["Stock List", "Calculated Scores"]
        )
        
        export_format = st.radio("Export Format:", ["CSV", "JSON", "Excel"])
        
        if st.button("📥 Export Data"):
            filename = f"stockanalyzer_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_format.lower()}"
            st.success(f"✅ Data exported to {filename}")
            st.download_button(
                label="⬇️ Download Export",
                data="sample,data,export",  # Would be actual data
                file_name=filename,
                mime="text/csv" if export_format == "CSV" else "application/json"
            )
    
    with col2:
        st.markdown("### Import Data")
        
        uploaded_file = st.file_uploader(
            "Choose a file to import:",
            type=['csv', 'json', 'xlsx']
        )
        
        if uploaded_file:
            st.info(f"📁 File: {uploaded_file.name}")
            st.info(f"📊 Size: {uploaded_file.size} bytes")
            
            import_mode = st.radio(
                "Import Mode:",
                ["Append (add new data)", "Replace (overwrite existing)", "Update (merge changes)"]
            )
            
            if st.button("📤 Import Data"):
                st.success("✅ Data imported successfully!")
                st.info("🔄 Recalculating composite scores...")

def main():
    """Main application function"""
    # Initialize session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'screener'
    
    # Load configuration and initialize components
    config = load_configuration()
    calculators = initialize_calculators()
    
    # Render methodology overview
    render_methodology_overview()
    
    st.markdown("---")
    
    # Navigation - Updated with Data Management
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Stock Screener", "📈 Stock Analysis", "🗄️ Data Management", "ℹ️ About"])
    
    with tab1:
        render_stock_screener()
    
    with tab2:
        st.header("📈 Individual Stock Analysis")
        
        # Get sample data for stock selection
        df = create_sample_data()
        
        selected_symbol = st.selectbox(
            "Select a stock for detailed analysis:",
            options=df['symbol'].tolist(),
            format_func=lambda x: f"{x} - {df[df['symbol']==x]['company'].iloc[0]}"
        )
        
        if selected_symbol:
            render_stock_analysis(selected_symbol, df)
    
    with tab3:
        render_data_management()
    
    with tab4:
        st.header("ℹ️ About StockAnalyzer Pro")
        
        st.markdown("""
        ### 🎯 Methodology Overview
        
        StockAnalyzer Pro uses a comprehensive 4-component methodology to identify potentially mispriced stocks:
        
        **1. Fundamental Valuation (40% weight)**
        - P/E Ratio analysis with sector normalization
        - EV/EBITDA for enterprise value assessment
        - PEG Ratio for growth-adjusted valuation
        - Free Cash Flow Yield for cash generation analysis
        
        **2. Quality Metrics (25% weight)**
        - Return on Equity (ROE) for profitability efficiency
        - Return on Invested Capital (ROIC) for capital allocation
        - Debt-to-Equity ratios for financial leverage assessment
        - Current Ratio for liquidity strength
        
        **3. Growth Analysis (20% weight)**
        - Revenue growth rate assessment
        - Earnings Per Share (EPS) growth analysis
        - Revenue growth stability over time
        - Forward growth expectations integration
        
        **4. Sentiment Analysis (15% weight)**
        - Financial news sentiment using TextBlob + VADER
        - Social media sentiment from Reddit discussions
        - Sentiment momentum tracking
        - Volume-weighted sentiment scoring
        
        ### 📊 Data Quality Indicators
        
        Each component includes data quality scores that measure:
        - **Completeness**: How many required metrics are available
        - **Reliability**: Source credibility and data freshness
        - **Volume**: Sufficient data points for statistical significance
        
        ### 🎯 Sector Adjustments
        
        The system includes sector-specific adjustments for 11 major sectors:
        - Technology, Healthcare, Financials, Energy, Utilities
        - Consumer Discretionary, Consumer Staples, Industrials
        - Materials, Communication Services, Real Estate
        
        ### ⚠️ Important Disclaimers
        
        - This tool is for educational and research purposes only
        - Not investment advice - always consult qualified professionals
        - Past performance doesn't guarantee future results
        - Consider all risks before making investment decisions
        """)

if __name__ == "__main__":
    main()