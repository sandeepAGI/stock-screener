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
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling with branding
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700&display=swap');
    
    /* Global font application */
    .main, .sidebar .sidebar-content, .stSelectbox, .stSlider, .stButton, 
    .stTextInput, .stMetric, .stMarkdown, h1, h2, h3, h4, h5, h6, p, div {
        font-family: 'Montserrat', sans-serif !important;
    }
    
    /* Header styling with brand color */
    .main-header {
        color: #60B5E5 !important;
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 700 !important;
        font-size: 2.5rem !important;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        font-family: 'Montserrat', sans-serif !important;
    }
    .undervalued {
        border-left: 4px solid #00ff00;
        background-color: #f0fff0;
        padding: 0.5rem;
        margin: 0.25rem 0;
        font-family: 'Montserrat', sans-serif !important;
    }
    .overvalued {
        border-left: 4px solid #ff0000;
        background-color: #fff0f0;
        padding: 0.5rem;
        margin: 0.25rem 0;
        font-family: 'Montserrat', sans-serif !important;
    }
    .stock-details {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        font-family: 'Montserrat', sans-serif !important;
    }
    
    /* Logo container */
    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 1rem;
    }
    
    .logo-container img {
        max-height: 80px;
        width: auto;
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
        AND cm.created_at = (
            SELECT MAX(created_at) FROM calculated_metrics cm2 
            WHERE cm2.symbol = cm.symbol
        )
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
        
        # Get recent news headlines (prefer articles with titles, deduplicated)
        news_query = """
        SELECT DISTINCT title, publish_date, sentiment_score, url
        FROM news_articles 
        WHERE symbol = ? 
        ORDER BY 
            CASE WHEN title IS NOT NULL AND LENGTH(title) > 0 THEN 0 ELSE 1 END,
            publish_date DESC 
        LIMIT 5
        """
        
        news_df = pd.read_sql_query(news_query, conn, params=[symbol])
        conn.close()
        
        return news_df
        
    except Exception as e:
        st.error(f"Error loading sentiment data: {e}")
        return pd.DataFrame()

def calculate_custom_composite_scores(df: pd.DataFrame, weights: List[float]) -> pd.DataFrame:
    """Recalculate composite scores with custom weights."""
    df_copy = df.copy()
    
    # Normalize weights to sum to 1
    weights = np.array(weights)
    weights = weights / weights.sum()
    
    # Calculate new composite scores
    df_copy['custom_composite_score'] = (
        df_copy['fundamental_score'] * weights[0] +
        df_copy['quality_score'] * weights[1] +
        df_copy['growth_score'] * weights[2] +
        df_copy['sentiment_score'] * weights[3]
    )
    
    # Calculate new rankings
    df_copy['custom_composite_rank'] = df_copy['custom_composite_score'].rank(ascending=False, method='min')
    df_copy['rank_change'] = df_copy['composite_rank'] - df_copy['custom_composite_rank']
    
    return df_copy.sort_values('custom_composite_score', ascending=False)

def get_database_stats() -> Dict:
    """Get basic database statistics for the summary."""
    try:
        conn = sqlite3.connect('data/stock_data.db')
        
        stats = {}
        
        # Count total stocks
        stats['total_stocks'] = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM stocks", conn
        ).iloc[0]['count']
        
        # Count stocks with calculations (latest only)
        stats['calculated_stocks'] = pd.read_sql_query(
            """SELECT COUNT(DISTINCT symbol) as count 
               FROM calculated_metrics 
               WHERE composite_score IS NOT NULL""", conn
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

def show_weight_adjusted_rankings(original_df: pd.DataFrame, adjusted_df: pd.DataFrame, weights: List[float]) -> None:
    """Display comparison of original vs weight-adjusted rankings."""
    st.subheader("📊 Weight-Adjusted Rankings Comparison")
    
    # Display current weights
    weight_labels = ["Fundamental", "Quality", "Growth", "Sentiment"]
    weights_normalized = np.array(weights) / np.sum(weights)
    
    cols = st.columns(4)
    for i, (label, weight) in enumerate(zip(weight_labels, weights_normalized)):
        with cols[i]:
            st.metric(f"{label}", f"{weight:.1%}")
    
    # Show top 10 comparison
    col_orig, col_adj = st.columns(2)
    
    with col_orig:
        st.markdown("**🏆 Original Rankings (40/25/20/15)**")
        top_orig = original_df.head(10)
        for idx, (_, row) in enumerate(top_orig.iterrows(), 1):
            st.write(f"{idx}. **{row['symbol']}** - {row['composite_score']:.1f}")
    
    with col_adj:
        st.markdown("**🎛️ Weight-Adjusted Rankings**")
        top_adj = adjusted_df.head(10)
        for idx, (_, row) in enumerate(top_adj.iterrows(), 1):
            rank_change = row['rank_change']
            if rank_change > 0:
                change_indicator = f"⬆️ +{int(rank_change)}"
                change_color = "🟢"
            elif rank_change < 0:
                change_indicator = f"⬇️ {int(rank_change)}"
                change_color = "🔴"
            else:
                change_indicator = "➡️ 0"
                change_color = "⚪"
            
            st.write(f"{idx}. **{row['symbol']}** - {row['custom_composite_score']:.1f} {change_color} {change_indicator}")
    
    # Highlight biggest movers
    st.subheader("📈 Biggest Ranking Changes")
    col_up, col_down = st.columns(2)
    
    with col_up:
        st.markdown("**📈 Biggest Gainers**")
        gainers = adjusted_df.nlargest(5, 'rank_change')
        for _, row in gainers.iterrows():
            if row['rank_change'] > 0:
                st.write(f"**{row['symbol']}**: Rank #{int(row['composite_rank'])} → #{int(row['custom_composite_rank'])} (⬆️ +{int(row['rank_change'])})")
    
    with col_down:
        st.markdown("**📉 Biggest Losers**")
        losers = adjusted_df.nsmallest(5, 'rank_change')
        for _, row in losers.iterrows():
            if row['rank_change'] < 0:
                st.write(f"**{row['symbol']}**: Rank #{int(row['composite_rank'])} → #{int(row['custom_composite_rank'])} (⬇️ {int(row['rank_change'])})")

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

def create_distribution_charts_custom(df: pd.DataFrame, score_column: str) -> Tuple[go.Figure, go.Figure]:
    """Create distribution charts for custom composite scores."""
    
    # Custom composite score histogram
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Histogram(
        x=df[score_column],
        nbinsx=25,
        name='Custom Composite Scores',
        marker_color='#ff6b35'  # Orange color to distinguish from original
    ))
    
    # Add mean line
    mean_score = df[score_column].mean()
    fig_hist.add_vline(x=mean_score, line_dash="dash", 
                       annotation_text=f"Mean: {mean_score:.1f}")
    
    fig_hist.update_layout(
        title="Custom Weighted Score Distribution (476 Stocks)",
        xaxis_title="Custom Composite Score",
        yaxis_title="Number of Stocks",
        height=400,
        showlegend=False
    )
    
    # Component box plots (same as original since components don't change)
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
        title="Component Score Distributions (Unchanged)",
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
            if sector_pct is not None and not pd.isna(sector_pct):
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
            # Filter for articles with actual titles
            valid_news = sentiment_data[sentiment_data['title'].notna() & (sentiment_data['title'].str.len() > 0)]
            if not valid_news.empty:
                st.subheader("Recent News Headlines")
                for _, news in valid_news.iterrows():
                    sentiment_color = "🟢" if news['sentiment_score'] > 0.1 else "🔴" if news['sentiment_score'] < -0.1 else "⚪"
                    st.write(f"{sentiment_color} **{news['title']}** _(Score: {news['sentiment_score']:.2f})_")
            else:
                st.subheader("Recent News Headlines")
                st.info("No recent news headlines available (news data collection needs refresh).")
        else:
            st.subheader("Recent News Headlines")
            st.info("No recent news headlines available for this stock.")
            
    except Exception as e:
        st.error(f"Error displaying detailed analysis: {e}")

def show_methodology_guide():
    """Display the methodology guide page."""
    st.title("📚 Methodology Guide")
    st.markdown("### Understanding Our 4-Component Stock Analysis System")
    
    # Overview section
    st.header("🎯 Overview")
    st.markdown("""
    Our stock analysis methodology evaluates companies using four key components, each weighted based on investment importance:
    
    - **🏢 Fundamental Analysis (40%)** - Traditional valuation metrics
    - **💎 Quality Metrics (25%)** - Financial health and efficiency  
    - **📈 Growth Analysis (20%)** - Revenue and earnings momentum
    - **💭 Sentiment Analysis (15%)** - Market perception and momentum
    
    Each component is scored 0-100, then combined into a weighted composite score for ranking.
    """)
    
    # Fundamental Analysis section
    st.header("🏢 Fundamental Analysis (40% Weight)")
    st.markdown("""
    **Purpose**: Identify stocks trading below their intrinsic value using traditional valuation metrics.
    
    **Key Metrics**:
    - **Price-to-Earnings (P/E) Ratio**: Lower P/E often indicates undervaluation
    - **Enterprise Value/EBITDA**: Measures company value relative to operating performance
    - **PEG Ratio**: P/E adjusted for growth rate (values < 1.0 often attractive)
    - **Free Cash Flow Yield**: Cash generation relative to market value
    
    **Scoring**: Lower valuation ratios typically receive higher scores, adjusted for sector norms.
    
    **Investment Insight**: High fundamental scores suggest stocks may be undervalued by traditional metrics.
    """)
    
    # Quality Metrics section
    st.header("💎 Quality Metrics (25% Weight)")
    st.markdown("""
    **Purpose**: Assess financial health, management efficiency, and business sustainability.
    
    **Key Metrics**:
    - **Return on Equity (ROE)**: How effectively management uses shareholder equity
    - **Return on Invested Capital (ROIC)**: Efficiency of capital allocation
    - **Debt-to-Equity Ratio**: Financial leverage and risk assessment
    - **Current Ratio**: Short-term liquidity and financial stability
    
    **Scoring**: Higher profitability ratios and lower debt levels receive higher scores.
    
    **Investment Insight**: High quality scores indicate companies with strong fundamentals and lower financial risk.
    """)
    
    # Growth Analysis section  
    st.header("📈 Growth Analysis (20% Weight)")
    st.markdown("""
    **Purpose**: Identify companies with strong growth momentum and future potential.
    
    **Key Metrics**:
    - **Revenue Growth Rate**: Top-line expansion over multiple periods
    - **Earnings Per Share (EPS) Growth**: Bottom-line improvement trends
    - **Growth Stability**: Consistency of growth patterns
    - **Forward Projections**: Analyst expectations for future growth
    
    **Scoring**: Higher and more consistent growth rates receive higher scores.
    
    **Investment Insight**: High growth scores suggest companies with expanding business models and earnings potential.
    """)
    
    # Sentiment Analysis section
    st.header("💭 Sentiment Analysis (15% Weight)")
    st.markdown("""
    **Purpose**: Capture market psychology, momentum, and emerging trends affecting stock perception.
    
    **Key Sources**:
    - **News Sentiment**: Analysis of financial news headlines and articles
    - **Social Media**: Reddit discussions and community sentiment  
    - **Trading Volume**: Market activity and institutional interest
    - **Analyst Revisions**: Professional outlook changes
    
    **Scoring**: Positive sentiment trends and increasing interest receive higher scores.
    
    **Investment Insight**: High sentiment scores may indicate building momentum or emerging opportunities.
    """)
    
    # Score Interpretation section
    st.header("📊 Score Interpretation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🟢 High Scores (70-100)")
        st.markdown("""
        **Interpretation**: Potentially undervalued opportunities
        - Strong fundamentals at reasonable prices
        - High-quality business operations  
        - Positive growth trajectories
        - Favorable market sentiment
        
        **Investment Consideration**: May warrant deeper analysis for long positions
        """)
    
    with col2:
        st.subheader("🔴 Low Scores (0-40)")
        st.markdown("""
        **Interpretation**: Potentially overvalued or problematic
        - Expensive relative to fundamentals
        - Quality concerns or high debt
        - Slowing or negative growth
        - Negative market sentiment
        
        **Investment Consideration**: May indicate caution or short opportunities
        """)
    
    # Detailed Metric Interpretation Guide
    st.header("🎯 Detailed Metric Interpretation")
    
    # Fundamental Metrics
    with st.expander("🏢 How to Read Fundamental Metrics (40% Weight)", expanded=False):
        st.markdown("""
        **P/E Ratio (Price-to-Earnings)**:
        - **15-25**: Generally reasonable valuation
        - **< 15**: Potentially undervalued (or declining business)
        - **> 25**: May be overvalued (or high-growth expectation)
        - **Negative**: Company is losing money
        
        **EV/EBITDA (Enterprise Value/Earnings)**:
        - **8-15**: Typical range for mature companies
        - **< 8**: Potentially cheap
        - **> 20**: Expensive or high-growth
        
        **PEG Ratio (P/E to Growth)**:
        - **< 1.0**: Attractive (P/E justified by growth)
        - **1.0-2.0**: Fair valuation
        - **> 2.0**: Potentially overvalued relative to growth
        
        **Free Cash Flow Yield**:
        - **> 8%**: Strong cash generation
        - **4-8%**: Decent cash flow
        - **< 4%**: Weak cash generation
        - **Negative**: Burning cash
        """)
    
    # Quality Metrics
    with st.expander("💎 How to Read Quality Metrics (25% Weight)", expanded=False):
        st.markdown("""
        **Return on Equity (ROE)**:
        - **> 20%**: Excellent management efficiency
        - **15-20%**: Good performance
        - **10-15%**: Average performance
        - **< 10%**: Below average efficiency
        
        **Return on Invested Capital (ROIC)**:
        - **> 15%**: Superior capital allocation
        - **10-15%**: Good capital efficiency
        - **5-10%**: Average returns
        - **< 5%**: Poor capital deployment
        
        **Debt-to-Equity Ratio**:
        - **< 0.3**: Conservative/Low debt
        - **0.3-0.6**: Moderate leverage
        - **0.6-1.0**: Higher leverage
        - **> 1.0**: High debt risk
        
        **Current Ratio (Short-term liquidity)**:
        - **> 2.0**: Strong liquidity position
        - **1.5-2.0**: Adequate liquidity
        - **1.0-1.5**: Tight but manageable
        - **< 1.0**: Liquidity concerns
        """)
    
    # Growth Metrics
    with st.expander("📈 How to Read Growth Metrics (20% Weight)", expanded=False):
        st.markdown("""
        **Revenue Growth Rate (Annual)**:
        - **> 20%**: High growth
        - **10-20%**: Strong growth
        - **5-10%**: Moderate growth
        - **0-5%**: Slow growth
        - **Negative**: Declining business
        
        **EPS Growth Rate (Annual)**:
        - **> 25%**: Excellent earnings growth
        - **15-25%**: Strong earnings expansion
        - **5-15%**: Steady earnings growth
        - **0-5%**: Slow earnings growth
        - **Negative**: Declining profitability
        
        **Growth Consistency**:
        - **High**: Predictable, stable growth patterns
        - **Medium**: Some volatility but positive trend
        - **Low**: Erratic or declining growth
        """)
    
    # Sentiment Metrics
    with st.expander("💭 How to Read Sentiment Metrics (15% Weight)", expanded=False):
        st.markdown("""
        **News Sentiment Score**:
        - **> 0.5**: Very positive news coverage
        - **0.1 to 0.5**: Positive sentiment
        - **-0.1 to 0.1**: Neutral coverage
        - **-0.5 to -0.1**: Negative sentiment
        - **< -0.5**: Very negative news
        
        **Sentiment Interpretation Examples**:
        - **0.84**: "Company soars on impressive earnings" 🟢
        - **0.25**: "Company reports solid quarterly results" 🟢
        - **0.00**: "Company announces quarterly results" ⚪
        - **-0.30**: "Company faces regulatory challenges" 🔴
        - **-0.70**: "Company plunges on disappointing guidance" 🔴
        
        **Volume & Momentum**:
        - **High Volume**: More mentions = higher confidence
        - **Positive Momentum**: Recent sentiment improving
        - **Negative Momentum**: Recent sentiment deteriorating
        """)
    
    # Composite Score Guide
    st.subheader("🎯 Composite Score Ranges")
    score_ranges = {
        "90-100": {"emoji": "🟢", "label": "Exceptional", "desc": "Top-tier investment opportunities with strong fundamentals across all metrics"},
        "80-89": {"emoji": "🟢", "label": "Excellent", "desc": "High-quality companies with attractive valuations and solid growth"},
        "70-79": {"emoji": "🟢", "label": "Good", "desc": "Solid investment candidates worth detailed analysis"},
        "60-69": {"emoji": "🟡", "label": "Above Average", "desc": "Decent opportunities but may have some concerns"},
        "50-59": {"emoji": "🟡", "label": "Average", "desc": "Mixed signals - requires careful evaluation"},
        "40-49": {"emoji": "🟡", "label": "Below Average", "desc": "Several red flags but not necessarily avoid"},
        "30-39": {"emoji": "🔴", "label": "Poor", "desc": "Significant concerns across multiple metrics"},
        "20-29": {"emoji": "🔴", "label": "Very Poor", "desc": "Major fundamental issues or severe overvaluation"},
        "0-19": {"emoji": "🔴", "label": "Avoid", "desc": "Critical problems - likely not suitable for investment"}
    }
    
    for score_range, info in score_ranges.items():
        st.markdown(f"**{info['emoji']} {score_range}: {info['label']}** - {info['desc']}")
    
    st.info("💡 **Remember**: These scores are screening tools. Always conduct additional research, consider your risk tolerance, and consult financial advisors before making investment decisions.")
    
    # Sector Adjustments section
    st.header("🏭 Sector Adjustments")
    st.markdown("""
    **Sector Context**: Different industries have varying normal ranges for financial metrics.
    
    **Examples**:
    - **Technology**: Often trades at higher P/E ratios due to growth expectations
    - **Utilities**: Typically lower growth but higher dividend yields
    - **Financial**: ROE and debt ratios interpreted differently
    - **Energy**: Commodity cycles affect valuation metrics
    
    **Our Approach**: Sector percentile rankings provide industry-relative context alongside absolute scores.
    """)
    
    # Weight Customization section
    st.header("🎛️ Weight Customization")
    st.markdown("""
    **Investment Philosophy Alignment**: Adjust component weights to match your investment style:
    
    - **Value Investing**: Increase Fundamental weight (50%+)
    - **Quality Focus**: Increase Quality weight (40%+) 
    - **Growth Investing**: Increase Growth weight (35%+)
    - **Momentum Trading**: Increase Sentiment weight (25%+)
    
    **Usage**: Use the sidebar sliders in the main dashboard to experiment with different weight combinations.
    """)
    
    # Limitations section
    st.header("⚠️ Important Limitations")
    st.markdown("""
    **This analysis should be considered alongside**:
    - Detailed fundamental analysis
    - Industry-specific factors
    - Macroeconomic conditions
    - Individual risk tolerance
    - Portfolio diversification needs
    
    **Disclaimer**: This tool is for educational and research purposes only. Not investment advice.
    """)

def main():
    """Main dashboard application."""
    
    # Page navigation
    st.sidebar.title("📊 Stock Outlier Analysis")
    page = st.sidebar.selectbox("Navigate", ["📈 Dashboard", "📚 Methodology Guide"])
    
    if page == "📚 Methodology Guide":
        show_methodology_guide()
        return
    
    # Initialize session state for slider values
    if 'reset_weights' not in st.session_state:
        st.session_state.reset_weights = False
    
    # Default weights (40/25/20/15)
    default_fund = 0.4
    default_qual = 0.25
    default_growth = 0.2
    default_sent = 0.15
    
    # Check if reset was requested
    if st.session_state.reset_weights:
        st.session_state.reset_weights = False
        # Clear any existing slider values from session state
        for key in list(st.session_state.keys()):
            if key.startswith('slider_'):
                del st.session_state[key]
    
    # Sidebar for weight adjustment (below navigation)
    with st.sidebar:
        st.markdown("---")
        st.header("🎛️ Adjust Component Weights")
        st.markdown("Modify the weights to see how it affects stock rankings:")
        
        # Sliders with unique keys for session state control
        fund_weight = st.slider(
            "🏢 Fundamental", 
            min_value=0.0, 
            max_value=0.8, 
            value=default_fund, 
            step=0.05,
            help="P/E, EV/EBITDA, PEG, FCF Yield",
            key="slider_fund"
        )
        
        qual_weight = st.slider(
            "💎 Quality", 
            min_value=0.0, 
            max_value=0.6, 
            value=default_qual, 
            step=0.05,
            help="ROE, ROIC, Debt Ratios, Current Ratio",
            key="slider_qual"
        )
        
        growth_weight = st.slider(
            "📈 Growth", 
            min_value=0.0, 
            max_value=0.5, 
            value=default_growth, 
            step=0.05,
            help="Revenue Growth, EPS Growth, Stability",
            key="slider_growth"
        )
        
        sent_weight = st.slider(
            "💭 Sentiment", 
            min_value=0.0, 
            max_value=0.4, 
            value=default_sent, 
            step=0.05,
            help="News Sentiment, Social Media, Volume",
            key="slider_sent"
        )
        
        # Show normalized weights
        custom_weights = [fund_weight, qual_weight, growth_weight, sent_weight]
        total_weight = sum(custom_weights)
        normalized_weights = [w/total_weight for w in custom_weights]
        
        st.markdown("**Normalized Weights:**")
        st.write(f"• Fundamental: {normalized_weights[0]:.1%}")
        st.write(f"• Quality: {normalized_weights[1]:.1%}")
        st.write(f"• Growth: {normalized_weights[2]:.1%}")
        st.write(f"• Sentiment: {normalized_weights[3]:.1%}")
        
        # Reset button
        if st.button("🔄 Reset to Default (40/25/20/15)"):
            st.session_state.reset_weights = True
            st.rerun()
    
    # Header with logo and brand styling
    try:
        # Create inline header with logo matching font size
        header_html = '''
        <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 1rem;">
            <img src="data:image/png;base64,{}" style="height: 2.5rem; margin-right: 15px;" />
            <h1 class="main-header" style="margin: 0;">Stock Outlier Analysis - S&P 500</h1>
        </div>
        '''
        
        # Read and encode the logo
        import base64
        with open("src/data/Logo-Element-Retina.png", "rb") as f:
            logo_data = base64.b64encode(f.read()).decode()
        
        st.markdown(header_html.format(logo_data), unsafe_allow_html=True)
    except:
        # Fallback if logo not found
        st.markdown('<h1 class="main-header">📊 Stock Outlier Analysis - S&P 500</h1>', unsafe_allow_html=True)
    st.markdown("### Professional Stock Mispricing Detection Dashboard")
    
    # Load data
    with st.spinner("Loading stock analysis data..."):
        df = load_stock_data()
        stats = get_database_stats()
    
    if df.empty:
        st.error("No data available. Please check database connection.")
        return
    
    # Check if weights have been adjusted
    default_weights = [0.4, 0.25, 0.2, 0.15]
    weights_changed = not np.allclose(normalized_weights, default_weights, atol=0.01)
    
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
    
    # Weight adjustment analysis section  
    if weights_changed:
        # Calculate custom composite scores
        df_adjusted = calculate_custom_composite_scores(df, normalized_weights)
        
        # Show weight-adjusted analysis
        show_weight_adjusted_rankings(df, df_adjusted, normalized_weights)
        
        # Use adjusted data for subsequent analysis
        main_df = df_adjusted
        score_column = 'custom_composite_score'
        st.info("📊 **Analysis below uses your custom weights.** Reset weights in sidebar to return to original methodology.")
    else:
        main_df = df
        score_column = 'composite_score'
    
    # Key findings section
    st.subheader("🎯 Key Investment Opportunities")
    
    col_under, col_over = st.columns(2)
    
    with col_under:
        if weights_changed:
            # Show custom weighted top stocks
            top_custom = main_df.head(5)
            st.subheader("🟢 TOP 5 UNDERVALUED STOCKS (Custom Weights)")
            for idx, (_, row) in enumerate(top_custom.iterrows(), 1):
                st.markdown(f"""
                <div class="undervalued">
                    <strong>#{idx} {row['symbol']} - {row['company_name']}</strong><br>
                    <em>{row['sector']} | Market Cap: ${row['market_cap_billions']:.1f}B</em><br>
                    <strong>Custom Score: {row['custom_composite_score']:.1f}</strong> (was {row['composite_score']:.1f})<br>
                    F: {row['fundamental_score']:.0f} | Q: {row['quality_score']:.0f} | G: {row['growth_score']:.0f} | S: {row['sentiment_score']:.0f}
                </div>
                """, unsafe_allow_html=True)
        else:
            show_top_stocks(df, top_n=5, ascending=False, title="🟢 TOP 5 UNDERVALUED STOCKS")
        st.caption("Higher scores indicate better fundamentals, quality, growth, and sentiment")
    
    with col_over:
        if weights_changed:
            # Show custom weighted bottom stocks
            bottom_custom = main_df.tail(5)[::-1]  # Reverse to show worst first
            st.subheader("🔴 TOP 5 OVERVALUED STOCKS (Custom Weights)")
            for idx, (_, row) in enumerate(bottom_custom.iterrows(), 1):
                st.markdown(f"""
                <div class="overvalued">
                    <strong>#{idx} {row['symbol']} - {row['company_name']}</strong><br>
                    <em>{row['sector']} | Market Cap: ${row['market_cap_billions']:.1f}B</em><br>
                    <strong>Custom Score: {row['custom_composite_score']:.1f}</strong> (was {row['composite_score']:.1f})<br>
                    F: {row['fundamental_score']:.0f} | Q: {row['quality_score']:.0f} | G: {row['growth_score']:.0f} | S: {row['sentiment_score']:.0f}
                </div>
                """, unsafe_allow_html=True)
        else:
            show_top_stocks(df, top_n=5, ascending=True, title="🔴 TOP 5 OVERVALUED STOCKS")
        st.caption("Lower scores may indicate overpricing or fundamental concerns")
    
    # Distribution analysis
    st.subheader("📈 Score Distribution Analysis")
    
    with st.spinner("Generating distribution charts..."):
        if weights_changed:
            # Create charts with custom scores
            fig_hist, fig_box = create_distribution_charts_custom(main_df, score_column)
        else:
            fig_hist, fig_box = create_distribution_charts(df)
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with chart_col2:
        st.plotly_chart(fig_box, use_container_width=True)
    
    # Statistical summary
    st.subheader("📊 Statistical Summary")
    summary_col1, summary_col2, summary_col3 = st.columns(3)
    
    # Use appropriate score column
    analysis_scores = main_df[score_column]
    
    with summary_col1:
        st.metric("Mean Score", f"{analysis_scores.mean():.1f}")
        st.metric("Std Deviation", f"{analysis_scores.std():.1f}")
    
    with summary_col2:
        st.metric("Median Score", f"{analysis_scores.median():.1f}")
        st.metric("Interquartile Range", f"{analysis_scores.quantile(0.75) - analysis_scores.quantile(0.25):.1f}")
    
    with summary_col3:
        # Outlier counts
        z_scores = np.abs((analysis_scores - analysis_scores.mean()) / analysis_scores.std())
        outliers = (z_scores > 2).sum()
        st.metric("Statistical Outliers", f"{outliers}", "Z-score > 2")
        
        # Percentile outliers  
        q1, q3 = analysis_scores.quantile([0.25, 0.75])
        iqr = q3 - q1
        percentile_outliers = ((analysis_scores < (q1 - 1.5 * iqr)) | 
                              (analysis_scores > (q3 + 1.5 * iqr))).sum()
        st.metric("Percentile Outliers", f"{percentile_outliers}", "IQR method")
    
    # Individual stock analysis
    st.subheader("🔍 Individual Stock Deep Dive")
    
    # Stock selector
    stock_options = [f"{row['symbol']} - {row['company_name']}" for _, row in main_df.iterrows()]
    selected_option = st.selectbox(
        "Select a stock for detailed analysis:",
        options=stock_options,
        index=0  # Default to first stock (highest composite score)
    )
    
    if selected_option:
        selected_symbol = selected_option.split(' - ')[0]
        show_stock_details(main_df, selected_symbol)
    
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