#!/usr/bin/env python3
"""
Stock Outlier Analytics Dashboard - Demo Version
Single-file Streamlit application for stakeholder presentation

Usage: streamlit run analytics_dashboard.py
"""

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
from typing import Optional, Dict, List, Tuple

# Page configuration
st.set_page_config(
    page_title="Stock Outlier Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .undervalued {
        border-left: 4px solid #00ff00;
        background-color: #f0fff0;
        padding: 0.5rem;
        margin: 0.25rem 0;
    }
    .overvalued {
        border-left: 4px solid #ff0000;
        background-color: #fff0f0;
        padding: 0.5rem;
        margin: 0.25rem 0;
    }
    .stock-details {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_stock_data() -> pd.DataFrame:
    """Load all stock data with calculated metrics from database."""
    try:
        conn = sqlite3.connect('data/stock_data.db')
        
        query = """
        SELECT 
            cm.symbol,
            s.company_name,
            s.sector,
            s.market_cap,
            cm.composite_score,
            cm.fundamental_score,
            cm.quality_score,
            cm.growth_score,
            cm.sentiment_score,
            cm.sector_percentile,
            cm.calculation_date,
            cm.methodology_version
        FROM calculated_metrics cm 
        JOIN stocks s ON cm.symbol = s.symbol
        WHERE cm.composite_score IS NOT NULL
        ORDER BY cm.composite_score DESC
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Add derived columns for analysis
        df['market_cap_billions'] = df['market_cap'] / 1e9
        df['composite_rank'] = df['composite_score'].rank(ascending=False, method='min')
        
        return df
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

@st.cache_data
def load_sentiment_data(symbol: str) -> pd.DataFrame:
    """Load sentiment details for a specific stock."""
    try:
        conn = sqlite3.connect('data/stock_data.db')
        
        # Get recent news headlines
        news_query = """
        SELECT title, publish_date, sentiment_score, url
        FROM news_articles 
        WHERE symbol = ? 
        ORDER BY publish_date DESC 
        LIMIT 5
        """
        
        news_df = pd.read_sql_query(news_query, conn, params=[symbol])
        conn.close()
        
        return news_df
        
    except Exception as e:
        st.error(f"Error loading sentiment data: {e}")
        return pd.DataFrame()

def get_database_stats() -> Dict:
    """Get basic database statistics for the summary."""
    try:
        conn = sqlite3.connect('data/stock_data.db')
        
        stats = {}
        
        # Count total stocks
        stats['total_stocks'] = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM stocks", conn
        ).iloc[0]['count']
        
        # Count stocks with calculations
        stats['calculated_stocks'] = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM calculated_metrics WHERE composite_score IS NOT NULL", conn
        ).iloc[0]['count']
        
        # Get last calculation date
        last_calc = pd.read_sql_query(
            "SELECT MAX(calculation_date) as last_date FROM calculated_metrics", conn
        ).iloc[0]['last_date']
        
        stats['last_calculation'] = last_calc
        
        # Coverage percentage
        stats['coverage_pct'] = (stats['calculated_stocks'] / stats['total_stocks']) * 100
        
        conn.close()
        return stats
        
    except Exception as e:
        st.error(f"Error getting database stats: {e}")
        return {'total_stocks': 0, 'calculated_stocks': 0, 'coverage_pct': 0, 'last_calculation': 'Unknown'}

def show_top_stocks(df: pd.DataFrame, top_n: int = 5, ascending: bool = False, title: str = "") -> None:
    """Display top N stocks in a formatted table."""
    if ascending:
        top_stocks = df.nsmallest(top_n, 'composite_score')
        container_class = "overvalued"
    else:
        top_stocks = df.nlargest(top_n, 'composite_score')
        container_class = "undervalued"
    
    st.subheader(title)
    
    for idx, (_, row) in enumerate(top_stocks.iterrows(), 1):
        st.markdown(f"""
        <div class="{container_class}">
            <strong>#{idx} {row['symbol']} - {row['company_name']}</strong><br>
            <em>{row['sector']} | Market Cap: ${row['market_cap_billions']:.1f}B</em><br>
            <strong>Composite Score: {row['composite_score']:.1f}</strong><br>
            F: {row['fundamental_score']:.0f} | Q: {row['quality_score']:.0f} | G: {row['growth_score']:.0f} | S: {row['sentiment_score']:.0f}
        </div>
        """, unsafe_allow_html=True)

def create_distribution_charts(df: pd.DataFrame) -> Tuple[go.Figure, go.Figure]:
    """Create histogram and box plot charts for score distributions."""
    
    # Composite score histogram using go.Figure for better compatibility
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Histogram(
        x=df['composite_score'],
        nbinsx=25,
        name='Composite Scores',
        marker_color='#1f77b4'
    ))
    
    # Add mean line
    mean_score = df['composite_score'].mean()
    fig_hist.add_vline(x=mean_score, line_dash="dash", 
                       annotation_text=f"Mean: {mean_score:.1f}")
    
    fig_hist.update_layout(
        title="Composite Score Distribution (476 Stocks)",
        xaxis_title="Composite Score",
        yaxis_title="Number of Stocks",
        height=400,
        showlegend=False
    )
    
    # Component box plots - simplified approach
    fig_box = go.Figure()
    
    components = ['Fundamental', 'Quality', 'Growth', 'Sentiment']
    colors = ['#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    for i, (component, color) in enumerate(zip(components, colors)):
        col_name = f'{component.lower()}_score'
        fig_box.add_trace(go.Box(
            y=df[col_name],
            name=component,
            marker_color=color
        ))
    
    fig_box.update_layout(
        title="Component Score Distributions",
        xaxis_title="Component",
        yaxis_title="Score",
        height=400,
        showlegend=False
    )
    
    return fig_hist, fig_box

def create_radar_chart(df: pd.DataFrame, symbol: str) -> go.Figure:
    """Create radar chart for individual stock component scores."""
    stock_data = df[df['symbol'] == symbol].iloc[0]
    
    components = ['Fundamental', 'Quality', 'Growth', 'Sentiment']
    scores = [
        stock_data['fundamental_score'],
        stock_data['quality_score'], 
        stock_data['growth_score'],
        stock_data['sentiment_score']
    ]
    
    # Add first point again to close the radar chart
    components_closed = components + [components[0]]
    scores_closed = scores + [scores[0]]
    
    fig = go.Figure(data=go.Scatterpolar(
        r=scores_closed,
        theta=components_closed,
        fill='toself',
        name=symbol,
        line_color='#1f77b4'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=False,
        title=f"{symbol} Component Breakdown",
        height=400
    )
    
    return fig

def show_stock_details(df: pd.DataFrame, symbol: str) -> None:
    """Display detailed information for a selected stock."""
    try:
        stock_data = df[df['symbol'] == symbol]
        if stock_data.empty:
            st.error(f"No data found for symbol: {symbol}")
            return
            
        stock_data = stock_data.iloc[0]
        
        # Basic info
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Composite Score", 
                f"{stock_data['composite_score']:.1f}",
                f"Rank: #{int(stock_data['composite_rank'])}"
            )
        
        with col2:
            sector_pct = stock_data['sector_percentile']
            if sector_pct is not None:
                st.metric("Sector Percentile", f"{sector_pct:.1f}%")
            else:
                st.metric("Sector Percentile", "N/A")
        
        with col3:
            st.metric(
                "Market Cap",
                f"${stock_data['market_cap_billions']:.1f}B"
            )
    except Exception as e:
        st.error(f"Error displaying stock details: {e}")
        return
    
    try:
        # Component scores in columns
        st.subheader("Component Scores")
        comp_col1, comp_col2, comp_col3, comp_col4 = st.columns(4)
        
        with comp_col1:
            st.metric("Fundamental (40%)", f"{stock_data['fundamental_score']:.0f}/100")
        with comp_col2:
            st.metric("Quality (25%)", f"{stock_data['quality_score']:.0f}/100")
        with comp_col3:
            st.metric("Growth (20%)", f"{stock_data['growth_score']:.0f}/100")
        with comp_col4:
            st.metric("Sentiment (15%)", f"{stock_data['sentiment_score']:.0f}/100")
        
        # Radar chart
        fig_radar = create_radar_chart(df, symbol)
        st.plotly_chart(fig_radar, use_container_width=True)
        
        # Sentiment details if available
        sentiment_data = load_sentiment_data(symbol)
        if not sentiment_data.empty:
            st.subheader("Recent News Headlines")
            for _, news in sentiment_data.iterrows():
                sentiment_color = "🟢" if news['sentiment_score'] > 0.1 else "🔴" if news['sentiment_score'] < -0.1 else "⚪"
                st.write(f"{sentiment_color} **{news['title']}** _(Score: {news['sentiment_score']:.2f})_")
        else:
            st.info("No recent news headlines available for this stock.")
            
    except Exception as e:
        st.error(f"Error displaying detailed analysis: {e}")

def main():
    """Main dashboard application."""
    
    # Header
    st.title("📊 Stock Outlier Analysis - S&P 500")
    st.markdown("### Professional Stock Mispricing Detection Dashboard")
    
    # Load data
    with st.spinner("Loading stock analysis data..."):
        df = load_stock_data()
        stats = get_database_stats()
    
    if df.empty:
        st.error("No data available. Please check database connection.")
        return
    
    # Summary metrics
    st.subheader("📋 Analysis Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Stocks Analyzed", 
            f"{stats['calculated_stocks']}/{stats['total_stocks']}", 
            f"{stats['coverage_pct']:.1f}%"
        )
    
    with col2:
        st.metric(
            "Data Quality", 
            "Enhanced",
            "v1.1 fallbacks"
        )
    
    with col3:
        st.metric(
            "Last Updated",
            stats['last_calculation'][:10] if stats['last_calculation'] else "Unknown"
        )
    
    with col4:
        st.metric(
            "Methodology",
            "4-Component",
            "40/25/20/15"
        )
    
    # Key findings section
    st.subheader("🎯 Key Investment Opportunities")
    
    col_under, col_over = st.columns(2)
    
    with col_under:
        show_top_stocks(df, top_n=5, ascending=False, title="🟢 TOP 5 UNDERVALUED STOCKS")
        st.caption("Higher scores indicate better fundamentals, quality, growth, and sentiment")
    
    with col_over:
        show_top_stocks(df, top_n=5, ascending=True, title="🔴 TOP 5 OVERVALUED STOCKS")
        st.caption("Lower scores may indicate overpricing or fundamental concerns")
    
    # Distribution analysis
    st.subheader("📈 Score Distribution Analysis")
    
    with st.spinner("Generating distribution charts..."):
        fig_hist, fig_box = create_distribution_charts(df)
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with chart_col2:
        st.plotly_chart(fig_box, use_container_width=True)
    
    # Statistical summary
    st.subheader("📊 Statistical Summary")
    summary_col1, summary_col2, summary_col3 = st.columns(3)
    
    with summary_col1:
        st.metric("Mean Score", f"{df['composite_score'].mean():.1f}")
        st.metric("Std Deviation", f"{df['composite_score'].std():.1f}")
    
    with summary_col2:
        st.metric("Median Score", f"{df['composite_score'].median():.1f}")
        st.metric("Interquartile Range", f"{df['composite_score'].quantile(0.75) - df['composite_score'].quantile(0.25):.1f}")
    
    with summary_col3:
        # Outlier counts
        z_scores = np.abs((df['composite_score'] - df['composite_score'].mean()) / df['composite_score'].std())
        outliers = (z_scores > 2).sum()
        st.metric("Statistical Outliers", f"{outliers}", "Z-score > 2")
        
        # Percentile outliers  
        q1, q3 = df['composite_score'].quantile([0.25, 0.75])
        iqr = q3 - q1
        percentile_outliers = ((df['composite_score'] < (q1 - 1.5 * iqr)) | 
                              (df['composite_score'] > (q3 + 1.5 * iqr))).sum()
        st.metric("Percentile Outliers", f"{percentile_outliers}", "IQR method")
    
    # Individual stock analysis
    st.subheader("🔍 Individual Stock Deep Dive")
    
    # Stock selector
    stock_options = [f"{row['symbol']} - {row['company_name']}" for _, row in df.iterrows()]
    selected_option = st.selectbox(
        "Select a stock for detailed analysis:",
        options=stock_options,
        index=0  # Default to first stock (highest composite score)
    )
    
    if selected_option:
        selected_symbol = selected_option.split(' - ')[0]
        show_stock_details(df, selected_symbol)
    
    # Sector analysis (optional)
    with st.expander("📊 Sector Analysis", expanded=False):
        sector_stats = df.groupby('sector').agg({
            'composite_score': ['mean', 'count'],
            'fundamental_score': 'mean',
            'quality_score': 'mean', 
            'growth_score': 'mean',
            'sentiment_score': 'mean'
        }).round(1)
        
        sector_stats.columns = ['Avg Composite', 'Stock Count', 'Avg Fund', 'Avg Quality', 'Avg Growth', 'Avg Sentiment']
        sector_stats = sector_stats.sort_values('Avg Composite', ascending=False)
        
        st.dataframe(sector_stats, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    **Methodology**: 4-component weighted analysis (Fundamental 40%, Quality 25%, Growth 20%, Sentiment 15%)  
    **Data Sources**: Yahoo Finance, Reddit API  
    **Last Updated**: {}  
    **⚠️ Disclaimer**: For educational purposes only. Not investment advice.
    """.format(stats['last_calculation'][:10] if stats['last_calculation'] else "Unknown"))

if __name__ == "__main__":
    main()