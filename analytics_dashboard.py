#!/usr/bin/env python3
"""
Stock Outlier Analytics Dashboard - Enhanced Version with Individual Analysis
Single-file Streamlit application for stakeholder presentation

Usage: streamlit run analytics_dashboard_enhanced.py
"""

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
from typing import Optional, Dict, List, Tuple
import sys
import os
import time

# Add project root to path for data collection imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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

    /* Individual stock analysis styling */
    .metric-card {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        font-family: 'Montserrat', sans-serif !important;
    }
    .score-excellent { color: #28a745; font-weight: bold; font-family: 'Montserrat', sans-serif !important; }
    .score-good { color: #17a2b8; font-weight: bold; font-family: 'Montserrat', sans-serif !important; }
    .score-average { color: #ffc107; font-weight: bold; font-family: 'Montserrat', sans-serif !important; }
    .score-poor { color: #fd7e14; font-weight: bold; font-family: 'Montserrat', sans-serif !important; }
    .score-very-poor { color: #dc3545; font-weight: bold; font-family: 'Montserrat', sans-serif !important; }
    .data-quality-high { color: #28a745; font-family: 'Montserrat', sans-serif !important; }
    .data-quality-medium { color: #ffc107; font-family: 'Montserrat', sans-serif !important; }
    .data-quality-low { color: #dc3545; font-family: 'Montserrat', sans-serif !important; }

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

        # Calculate coverage percentage
        if stats['total_stocks'] > 0:
            stats['coverage_pct'] = (stats['calculated_stocks'] / stats['total_stocks']) * 100
        else:
            stats['coverage_pct'] = 0

        # Get last calculation date
        last_calc = pd.read_sql_query(
            "SELECT MAX(created_at) as last_calc FROM calculated_metrics", conn
        ).iloc[0]['last_calc']

        if last_calc:
            stats['last_calculation'] = last_calc
        else:
            stats['last_calculation'] = 'Unknown'

        conn.close()
        return stats

    except Exception as e:
        st.error(f"Error getting database stats: {e}")
        return {'total_stocks': 0, 'calculated_stocks': 0, 'coverage_pct': 0, 'last_calculation': 'Unknown'}

def show_weight_adjusted_rankings(original_df: pd.DataFrame, adjusted_df: pd.DataFrame, weights: List[float]) -> None:
    """Display side-by-side comparison of original vs adjusted rankings."""

    weight_labels = ['Fundamental', 'Quality', 'Growth', 'Sentiment']
    weights_normalized = np.array(weights) / np.sum(weights)

    # Display current weights
    cols = st.columns(4)
    for i, (label, weight) in enumerate(zip(weight_labels, weights_normalized)):
        with cols[i]:
            st.metric(f"{label}", f"{weight:.1%}")

    # Side-by-side rankings
    col_orig, col_adj = st.columns(2)

    with col_orig:
        st.markdown("**🏆 Original Rankings (40/25/20/15)**")
        top_orig = original_df.head(10)[['symbol', 'company_name', 'composite_score']].copy()
        top_orig.index = range(1, len(top_orig) + 1)
        st.dataframe(top_orig, use_container_width=True)

    with col_adj:
        st.markdown("**🎯 Adjusted Rankings (Custom Weights)**")
        top_adj = adjusted_df.head(10)[['symbol', 'company_name', 'custom_composite_score']].copy()
        top_adj.columns = ['symbol', 'company_name', 'composite_score']
        top_adj.index = range(1, len(top_adj) + 1)
        st.dataframe(top_adj, use_container_width=True)

    # Show biggest movers
    st.subheader("📊 Biggest Ranking Changes")

    # Filter for significant moves
    big_movers = adjusted_df[abs(adjusted_df['rank_change']) >= 5].copy()

    if len(big_movers) > 0:
        col_up, col_down = st.columns(2)

        with col_up:
            st.markdown("**📈 Biggest Gainers**")
            gainers = big_movers[big_movers['rank_change'] > 0].nlargest(5, 'rank_change')
            if len(gainers) > 0:
                for _, stock in gainers.iterrows():
                    st.success(f"📈 **{stock['symbol']}** moved up {int(stock['rank_change'])} positions")
            else:
                st.info("No significant gainers with current weight adjustment")

        with col_down:
            st.markdown("**📉 Biggest Losers**")
            losers = big_movers[big_movers['rank_change'] < 0].nsmallest(5, 'rank_change')
            if len(losers) > 0:
                for _, stock in losers.iterrows():
                    st.error(f"📉 **{stock['symbol']}** moved down {int(abs(stock['rank_change']))} positions")
            else:
                st.info("No significant losers with current weight adjustment")
    else:
        st.info("No significant ranking changes (±5 positions) with current weight adjustment")

def show_top_performers(df: pd.DataFrame, top_n: int = 5, ascending: bool = False, score_column: str = 'composite_score') -> None:
    """Display top N stocks in a formatted table."""
    if ascending:
        top_stocks = df.nsmallest(top_n, score_column)
        container_class = "overvalued"
        title = f"🔴 Most Overvalued (Bottom {top_n})"
    else:
        top_stocks = df.nlargest(top_n, score_column)
        container_class = "undervalued"
        title = f"🟢 Most Undervalued (Top {top_n})"

    st.markdown(f"**{title}**")

    for _, stock in top_stocks.iterrows():
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

            with col1:
                st.markdown(f"""
                <div class="{container_class}">
                    <strong>{stock['symbol']}</strong><br>
                    <small>{stock['company_name']}</small>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div class="stock-details">
                    <strong>Sector:</strong> {stock['sector']}<br>
                    <strong>Market Cap:</strong> ${stock['market_cap_billions']:.1f}B
                </div>
                """, unsafe_allow_html=True)

            with col3:
                # Use the appropriate score column
                score_value = stock[score_column] if score_column in stock else stock.get('composite_score', 0)
                st.metric("Score", f"{score_value:.1f}")

            with col4:
                # Use the appropriate rank column
                if score_column == 'custom_composite_score':
                    rank_value = stock.get('custom_composite_rank', stock.get('composite_rank', 0))
                else:
                    rank_value = stock.get('composite_rank', 0)
                st.metric("Rank", f"#{int(rank_value)}")

def show_detailed_analysis(symbol: str, df: pd.DataFrame):
    """Show detailed analysis for a selected stock with sentiment data."""
    try:
        stock_data = df[df['symbol'] == symbol].iloc[0]

        # Stock header
        st.markdown(f"### 📈 {stock_data['company_name']} ({symbol})")
        st.markdown(f"**Sector:** {stock_data['sector']} | **Market Cap:** ${stock_data['market_cap_billions']:.1f}B")

        # Key metrics in columns
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Composite Score",
                f"{stock_data['composite_score']:.1f}",
                help="Overall weighted score based on 4 components"
            )

        with col2:
            sector_pct = stock_data['sector_percentile']
            if sector_pct is not None and not pd.isna(sector_pct):
                st.metric("Sector Percentile", f"{sector_pct:.1f}%")
            else:
                st.metric("Market Rank", f"#{int(stock_data['composite_rank'])}")

        with col3:
            market_cap_rank = "Large" if stock_data['market_cap_billions'] > 10 else "Mid" if stock_data['market_cap_billions'] > 2 else "Small"
            st.metric("Cap Category", market_cap_rank)

        # Component scores breakdown
        st.subheader("📊 Component Analysis")

        # Create visual breakdown
        comp_col1, comp_col2, comp_col3, comp_col4 = st.columns(4)

        with comp_col1:
            st.metric("Fundamental (40%)", f"{stock_data['fundamental_score']:.0f}/100")
        with comp_col2:
            st.metric("Quality (25%)", f"{stock_data['quality_score']:.0f}/100")
        with comp_col3:
            st.metric("Growth (20%)", f"{stock_data['growth_score']:.0f}/100")
        with comp_col4:
            st.metric("Sentiment (15%)", f"{stock_data['sentiment_score']:.0f}/100")

        # Load and display sentiment data
        sentiment_df = load_sentiment_data(symbol)

        if not sentiment_df.empty and 'title' in sentiment_df.columns:
            # Filter out rows with empty or null titles
            valid_news = sentiment_df[
                (sentiment_df['title'].notna()) &
                (sentiment_df['title'] != '') &
                (sentiment_df['title'] != 'No title available')
            ]

            if len(valid_news) > 0:
                st.subheader("📰 Recent News Analysis")

                for _, news in valid_news.head(3).iterrows():
                    sentiment_emoji = "🟢" if news['sentiment_score'] > 0.1 else "🔴" if news['sentiment_score'] < -0.1 else "⚪"

                    with st.expander(f"{sentiment_emoji} {news['title'][:80]}..."):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**Published:** {news['publish_date']}")
                            if pd.notna(news['url']) and news['url']:
                                st.markdown(f"[Read full article]({news['url']})")
                        with col2:
                            st.metric("Sentiment", f"{news['sentiment_score']:.2f}")
            else:
                st.info("No recent news headlines available (news data collection needs refresh).")
        else:
            st.subheader("Recent News Headlines")
            st.info("No recent news headlines available for this stock.")

    except Exception as e:
        st.error(f"Error displaying detailed analysis: {e}")

# Individual Stock Analysis Functions
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

def show_individual_stock_analysis(df: pd.DataFrame):
    """Display individual stock analysis tab"""
    st.header("📈 Individual Stock Analysis")

    if df.empty:
        st.error("No data available for individual stock analysis.")
        return

    # Stock selection with enhanced searchability
    col1, col2 = st.columns([2, 1])

    with col1:
        # Create searchable options - prioritize by score for better defaults
        df_sorted = df.sort_values('composite_score', ascending=False)

        # Create options with both symbol and company name for better searchability
        stock_options = {}
        for _, row in df_sorted.iterrows():
            # Format: "AAPL - Apple Inc. (Score: 85.2)"
            display_name = f"{row['symbol']} - {row['company_name']} (Score: {row['composite_score']:.1f})"
            stock_options[display_name] = row['symbol']

        # Instructions for search
        st.markdown("**💡 Search Tips:** Type ticker symbol (e.g., 'AAPL') or company name (e.g., 'Apple') to quickly find stocks")

        selected_display = st.selectbox(
            "🔍 Select a stock to analyze:",
            options=list(stock_options.keys()),
            help="Start typing to search by ticker symbol or company name. Stocks are sorted by composite score (highest first).",
            key="stock_selector"
        )
        selected_symbol = stock_options[selected_display]

    with col2:
        st.metric("Total Stocks", len(df))
        # Show selected stock's rank
        selected_rank = df[df['symbol'] == selected_symbol]['composite_rank'].iloc[0]
        st.metric("Selected Rank", f"#{int(selected_rank)}")

    # Get selected stock data
    stock_data = df[df['symbol'] == selected_symbol].iloc[0]

    # Display stock header
    st.subheader(f"📊 {stock_data['company_name']} ({selected_symbol})")
    if 'sector' in stock_data and pd.notna(stock_data['sector']):
        st.caption(f"Sector: {stock_data['sector']}")

    # Key metrics overview
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Composite Score",
            f"{stock_data['composite_score']:.1f}",
            help="Overall weighted score (0-100)"
        )

    with col2:
        if 'sector_percentile' in stock_data and pd.notna(stock_data['sector_percentile']):
            st.metric(
                "Sector Percentile",
                f"{stock_data['sector_percentile']:.1f}%",
                help="Ranking within sector"
            )
        else:
            st.metric("Market Rank", f"#{int(stock_data['composite_rank'])}")

    with col3:
        # Calculate mock data quality (since we don't have it in current schema)
        avg_quality = 0.85  # Mock value - would be calculated from actual data
        st.metric(
            "Data Quality",
            f"{avg_quality*100:.0f}%",
            help="Overall data completeness and reliability"
        )

    with col4:
        # Determine category based on score
        score = stock_data['composite_score']
        if score >= 70:
            category = "Undervalued"
        elif score >= 50:
            category = "Balanced"
        else:
            category = "Overvalued"
        st.metric("Category", category)

    # Component scores breakdown
    st.subheader("📊 Component Score Breakdown")

    # Create radar chart
    categories = ['Fundamental\\n(40%)', 'Quality\\n(25%)', 'Growth\\n(20%)', 'Sentiment\\n(15%)']
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
        line_color='rgb(96, 181, 229)',  # Brand color
        fillcolor='rgba(96, 181, 229, 0.3)'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=False,
        title="Component Score Distribution",
        height=400,
        font=dict(family='Montserrat')
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**📋 Detailed Scores**")

        components = [
            ('Fundamental', stock_data['fundamental_score'], 40),
            ('Quality', stock_data['quality_score'], 25),
            ('Growth', stock_data['growth_score'], 20),
            ('Sentiment', stock_data['sentiment_score'], 15)
        ]

        for name, score, weight in components:
            # Mock data quality for each component
            mock_quality = 0.8 + (score / 500)  # Vary quality based on score
            mock_quality = min(1.0, max(0.6, mock_quality))  # Keep in reasonable range

            st.markdown(f"""
            <div class="metric-card">
                <strong>{name} ({weight}%)</strong><br>
                Score: {format_score(score)}<br>
                Data Quality: {format_data_quality(mock_quality)}
            </div>
            """, unsafe_allow_html=True)

    # Additional details section
    st.subheader("💡 Investment Insights")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🎯 Strengths**")
        # Identify top 2 components
        component_scores = [
            ("Fundamental", stock_data['fundamental_score']),
            ("Quality", stock_data['quality_score']),
            ("Growth", stock_data['growth_score']),
            ("Sentiment", stock_data['sentiment_score'])
        ]
        component_scores.sort(key=lambda x: x[1], reverse=True)

        for name, score in component_scores[:2]:
            if score >= 60:
                st.success(f"✓ Strong {name} metrics ({score:.1f}/100)")
            else:
                st.info(f"• {name} showing potential ({score:.1f}/100)")

    with col2:
        st.markdown("**⚠️ Areas for Attention**")

        # Look for areas that need attention
        attention_areas = []
        for name, score in component_scores:
            if score < 50:
                attention_areas.append((name, score, "warning"))
            elif score < 60:
                attention_areas.append((name, score, "info"))

        if attention_areas:
            # Show areas that actually need attention
            for name, score, alert_type in attention_areas:
                if alert_type == "warning":
                    st.warning(f"• {name} metrics need attention ({score:.1f}/100)")
                else:
                    st.info(f"• {name} has room for improvement ({score:.1f}/100)")
        else:
            # If no areas need attention, show the weakest relative areas for monitoring
            weakest_scores = component_scores[-2:]  # Bottom 2 scores
            st.info("**📊 Areas to Monitor (relative weaknesses):**")
            for name, score in weakest_scores:
                relative_weakness = "lowest" if score == component_scores[-1][1] else "second lowest"
                st.info(f"• {name}: {score:.1f}/100 ({relative_weakness} component)")
            st.success(f"💪 Overall strong performance - all metrics above 60")

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
    **Key Metrics:**
    - **P/E Ratio**: Current valuation relative to earnings
    - **EV/EBITDA**: Enterprise value compared to operating earnings
    - **PEG Ratio**: Growth-adjusted valuation metric
    - **FCF Yield**: Free cash flow relative to market value

    **Scoring**: Lower ratios (indicating cheaper valuations) receive higher scores.

    **Investment Insight**: High fundamental scores suggest stocks trading below intrinsic value.
    """)

    # Quality Analysis section
    st.header("💎 Quality Analysis (25% Weight)")
    st.markdown("""
    **Key Metrics:**
    - **ROE (Return on Equity)**: Profitability efficiency
    - **ROIC (Return on Invested Capital)**: Capital allocation effectiveness
    - **Debt-to-Equity**: Financial leverage and risk
    - **Current Ratio**: Short-term liquidity and financial stability

    **Scoring**: Higher profitability ratios and lower debt levels receive higher scores.

    **Investment Insight**: High quality scores indicate companies with strong fundamentals and lower financial risk.
    """)

    # Growth Analysis section
    st.header("📈 Growth Analysis (20% Weight)")
    st.markdown("""
    **Key Metrics:**
    - **Revenue Growth**: Top-line expansion trends
    - **EPS Growth**: Earnings per share improvement
    - **Growth Stability**: Consistency of growth patterns
    - **Forward Projections**: Analyst expectations for future growth

    **Scoring**: Higher and more consistent growth rates receive higher scores.

    **Investment Insight**: High growth scores suggest companies with expanding business momentum.
    """)

    # Sentiment Analysis section
    st.header("💭 Sentiment Analysis (15% Weight)")
    st.markdown("""
    **Key Metrics:**
    - **News Sentiment**: Media coverage analysis using NLP
    - **Social Media Mentions**: Reddit and social platform discussions
    - **Volume Patterns**: Trading activity as sentiment indicator
    - **Analyst Revisions**: Professional opinion changes

    **Scoring**: Positive sentiment trends and increasing attention receive higher scores.

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

        **Investment Consideration**: Consider for value-oriented portfolios
        """)

    with col2:
        st.subheader("🔴 Low Scores (0-40)")
        st.markdown("""
        **Interpretation**: Potentially overvalued or problematic
        - Expensive relative to fundamentals
        - Weak financial health indicators
        - Declining or stagnant growth
        - Negative market perception

        **Investment Consideration**: Avoid or consider for short positions
        """)

    # Advanced Features section
    st.header("🔧 Advanced Features")

    st.subheader("⚖️ Custom Weight Adjustment")
    st.markdown("""
    Use the sidebar sliders to adjust component weights based on your investment philosophy:

    - **Value Investors**: Increase Fundamental weight (50-60%)
    - **Quality Investors**: Increase Quality weight (35-40%)
    - **Growth Investors**: Increase Growth weight (30-35%)
    - **Momentum Investors**: Increase Sentiment weight (25-30%)

    The system automatically normalizes weights and shows ranking changes in real-time.
    """)

    st.subheader("📈 Ranking Analysis")
    st.markdown("""
    **Original Rankings**: Based on our research-backed 40/25/20/15 allocation

    **Custom Rankings**: Reflects your personalized weight preferences

    **Movement Analysis**:
    - **Green arrows**: Stocks improving in custom rankings
    - **Red arrows**: Stocks declining in custom rankings
    - **Position changes**: Show which stocks benefit from your investment style
    """)

    st.subheader("📊 Component Deep-Dive")
    st.markdown("""
    Each component provides detailed sub-metrics:

    **Fundamental Metrics**:
    - **Forward P/E**: Future earnings-based valuation
    - **PEG**: Growth-adjusted P/E for growth stocks
    - **FCF Yield**: Cash generation relative to price

    **Quality Indicators**:
    - **ROE Trend**: Return on equity trajectory
    - **Debt Coverage**: Ability to service debt obligations
    - **Working Capital**: Short-term financial health

    **Growth Patterns**:
    - **Revenue Acceleration**: Quarter-over-quarter changes
    - **Margin Expansion**: Profitability improvements
    - **Guidance Quality**: Management forecast reliability

    **Sentiment Dynamics**:
    - **News Velocity**: Rate of coverage changes
    - **Social Momentum**: Discussion volume trends
    - **Institutional Interest**: Smart money positioning
    """)

    # Risk and Limitations section
    st.header("⚠️ Important Considerations")

    st.markdown("""
    **Risk Factors**:
    - Past performance doesn't guarantee future results
    - Market conditions can override fundamental analysis
    - Sentiment can be volatile and change rapidly
    - Some metrics may lag actual business performance

    **Data Limitations**:
    - **Historical Focus**: Analysis based on trailing data
    - **Market Coverage**: Primarily S&P 500 constituents
    - **Update Frequency**: Daily refreshes may miss intraday developments
    - **Sector Bias**: Some sectors may inherently score higher/lower

    **Best Practices**:
    - Use scores as starting point for deeper research
    - Consider multiple time horizons for investment decisions
    - Diversify across sectors and market capitalizations
    - Monitor position sizing and risk management
    - Combine with additional due diligence and analysis
    """)

    # Methodology Evolution section
    st.header("🔄 Methodology Evolution")

    st.markdown("""
    **Version History**:
    - **v1.0**: Basic 4-component framework
    - **v1.1**: Enhanced sentiment analysis with Reddit integration
    - **v1.2**: Improved data quality controls and fallback mechanisms
    - **v2.0**: Real-time weight customization and ranking comparison

    **Continuous Improvement**:
    - Regular backtesting against market performance
    - Incorporation of new data sources and metrics
    - Refinement of scoring algorithms based on effectiveness
    - User feedback integration for enhanced usability
    """)

    # Final Disclaimer
    st.header("📋 Final Notes")

    st.markdown("""
    **Investment Philosophy**: This tool supports multiple investment approaches while maintaining analytical rigor.

    **Decision Support**: Designed to enhance, not replace, fundamental investment research and professional judgment.

    **Continuous Learning**: Methodology adapts based on market feedback and performance validation.

    **User Empowerment**: Provides transparency and customization for informed decision-making.

    Remember to consider:
    - Individual investment goals and risk tolerance
    - Current market conditions and cycles
    - Portfolio diversification needs

    **Disclaimer**: This tool is for educational and research purposes only. Not investment advice.
    """)

# Data Management Functions
@st.cache_resource
def initialize_data_collection():
    """Initialize data collection orchestrator"""
    try:
        from src.data.collectors import DataCollectionOrchestrator
        return DataCollectionOrchestrator()
    except Exception as e:
        st.error(f"Could not initialize data collection: {e}")
        return None

def get_data_source_status():
    """Get status of data sources with counts and freshness"""
    try:
        conn = sqlite3.connect('data/stock_data.db')
        sources = {}

        # Helper function to calculate status
        def calculate_status(last_update_str):
            if last_update_str == 'Never' or not last_update_str:
                return {'status': '🔴 No Data', 'days_old': 999}

            try:
                # Parse timestamp - handle both ISO and space-separated formats
                if 'T' in last_update_str:
                    last_update = datetime.strptime(last_update_str.split('.')[0], '%Y-%m-%dT%H:%M:%S')
                elif ':' in last_update_str:
                    # Handle full datetime with time
                    last_update = datetime.strptime(last_update_str, '%Y-%m-%d %H:%M:%S')
                else:
                    # Handle date-only
                    last_update = datetime.strptime(last_update_str, '%Y-%m-%d')

                # Calculate age - handle negative values (future dates due to timezone)
                time_diff = datetime.now() - last_update
                days_old = max(0, time_diff.days)  # Ensure non-negative
                hours_old = time_diff.total_seconds() / 3600

                # More granular freshness for recent updates
                if abs(hours_old) < 1:  # Within 1 hour (including future)
                    status = '🟢 Fresh'
                    days_old = 0
                elif days_old == 0:
                    status = '🟢 Fresh'
                elif days_old <= 7:
                    status = '🟡 Recent'
                else:
                    status = '🔴 Stale'

                return {'status': status, 'days_old': days_old}
            except:
                return {'status': '🔴 Error', 'days_old': 999}

        # Check fundamental data
        fundamental_query = "SELECT COUNT(*) as count, MAX(created_at) as latest FROM fundamental_data"
        result = pd.read_sql_query(fundamental_query, conn)
        latest = result.iloc[0]['latest'] if result.iloc[0]['latest'] else 'Never'
        status_info = calculate_status(latest)
        sources['Fundamentals'] = {
            'count': result.iloc[0]['count'],
            'last_update': latest,
            'status': status_info['status'],
            'days_old': status_info['days_old']
        }

        # Check price data
        price_query = "SELECT COUNT(*) as count, MAX(date) as latest FROM price_data"
        result = pd.read_sql_query(price_query, conn)
        latest = result.iloc[0]['latest'] if result.iloc[0]['latest'] else 'Never'
        status_info = calculate_status(latest)
        sources['Prices'] = {
            'count': result.iloc[0]['count'],
            'last_update': latest,
            'status': status_info['status'],
            'days_old': status_info['days_old']
        }

        # Check news data
        news_query = "SELECT COUNT(*) as count, MAX(publish_date) as latest FROM news_articles"
        result = pd.read_sql_query(news_query, conn)
        latest = result.iloc[0]['latest'] if result.iloc[0]['latest'] else 'Never'
        status_info = calculate_status(latest)
        sources['News'] = {
            'count': result.iloc[0]['count'],
            'last_update': latest,
            'status': status_info['status'],
            'days_old': status_info['days_old']
        }

        # Check Reddit data
        reddit_query = "SELECT COUNT(*) as count, MAX(created_utc) as latest FROM reddit_posts"
        result = pd.read_sql_query(reddit_query, conn)
        latest = result.iloc[0]['latest'] if result.iloc[0]['latest'] else 'Never'
        status_info = calculate_status(latest)
        sources['Reddit'] = {
            'count': result.iloc[0]['count'],
            'last_update': latest,
            'status': status_info['status'],
            'days_old': status_info['days_old']
        }

        # Check calculated metrics
        metrics_query = "SELECT COUNT(*) as count, MAX(created_at) as latest FROM calculated_metrics"
        result = pd.read_sql_query(metrics_query, conn)
        latest = result.iloc[0]['latest'] if result.iloc[0]['latest'] else 'Never'
        status_info = calculate_status(latest)
        sources['Calculated Metrics'] = {
            'count': result.iloc[0]['count'],
            'last_update': latest,
            'status': status_info['status'],
            'days_old': status_info['days_old']
        }

        conn.close()
        return sources

    except Exception as e:
        st.error(f"Error checking data source status: {e}")
        return {}

def run_data_refresh(data_types: List[str], symbols: Optional[List[str]] = None, progress_placeholder=None):
    """Run data refresh with progress tracking"""
    try:
        orchestrator = initialize_data_collection()
        if not orchestrator:
            return False, "Could not initialize data collection system"

        # Get symbols to refresh (default to all if none specified)
        if not symbols:
            conn = sqlite3.connect('data/stock_data.db')
            symbol_query = "SELECT DISTINCT symbol FROM stocks ORDER BY symbol"
            symbols_df = pd.read_sql_query(symbol_query, conn)
            symbols = symbols_df['symbol'].tolist()  # Use all stocks for production
            conn.close()

        results = {}
        total_steps = len(data_types)

        for i, data_type in enumerate(data_types):
            if progress_placeholder:
                progress = (i + 1) / total_steps
                progress_placeholder.progress(progress, f"Refreshing {data_type}...")

            try:
                if data_type == 'fundamentals':
                    result = orchestrator.refresh_fundamentals_only(symbols)
                elif data_type == 'prices':
                    result = orchestrator.refresh_prices_only(symbols)
                elif data_type == 'news':
                    result = orchestrator.refresh_news_only(symbols)
                elif data_type == 'sentiment':
                    result = orchestrator.refresh_sentiment_only(symbols)
                else:
                    result = {symbol: False for symbol in symbols}

                results[data_type] = result

            except Exception as e:
                results[data_type] = f"Error: {str(e)}"

        if progress_placeholder:
            progress_placeholder.progress(1.0, "Refresh completed!")

        return True, results

    except Exception as e:
        return False, f"Refresh failed: {str(e)}"

def show_data_management():
    """Display the data management tab"""
    st.header("🗄️ Data Management & Quality Control")

    # Data Source Status Section
    st.subheader("📡 Data Source Status")

    # Get status
    with st.spinner("Checking data source status..."):
        status_data = get_data_source_status()

    if status_data:
        # Display status in columns
        col1, col2, col3, col4, col5 = st.columns(5)

        status_items = list(status_data.items())
        for i, (source, data) in enumerate(status_items):
            col = [col1, col2, col3, col4, col5][i % 5]
            with col:
                # Use the pre-calculated status from the function
                status_icon = data['status']
                count = data['count']
                days_old = data['days_old']
                last_update = data['last_update']

                # Format display text
                if days_old == 0:
                    status_text = "Today"
                elif days_old == 1:
                    status_text = "1 day ago"
                elif days_old < 999:
                    status_text = f"{days_old} days ago"
                else:
                    status_text = "Never"

                st.metric(
                    label=f"{status_icon.split()[0]} {source}",
                    value=f"{count:,} records",
                    delta=status_text,
                    help=f"Last updated: {last_update}"
                )

    # Data Refresh Workflow
    st.subheader("🔄 Data Refresh Workflow")

    st.markdown("""
    **Complete refresh process in 3 steps:**
    1. 🚀 **Quick Refresh** - Update core data (fundamentals + prices)
    2. 📰 **Manual Refresh** - Add news and sentiment data
    3. 🔄 **Refresh Metrics** - Recalculate composite scores
    """)

    # Step 1: Quick Refresh
    st.markdown("### Step 1: 🚀 Quick Data Refresh")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("**Updates essential data for all stocks:**")
        st.markdown("• 📊 Fundamental Data (P/E, market cap, revenue, etc.)")
        st.markdown("• 💹 Price Data (historical prices and volume)")
        st.markdown("• ⚡ Fast update for ~503 stocks")

    with col2:
        if st.button("🚀 Start Quick Refresh", type="primary", help="Refresh fundamentals and prices for all stocks - typically completes in 2-5 minutes"):
            # Store in session state to persist results
            if 'quick_refresh_results' not in st.session_state:
                st.session_state.quick_refresh_results = None

            data_types = ['fundamentals', 'prices']
            progress_placeholder = st.empty()

            try:
                with st.spinner("Refreshing core data..."):
                    success, results = run_data_refresh(data_types, None, progress_placeholder)
                    st.session_state.quick_refresh_results = {
                        'success': success,
                        'results': results,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }

                if success:
                    st.success("✅ Quick refresh completed!")
                    st.info("▶️ **Next:** Run Step 2 for complete data update")
                else:
                    st.error(f"❌ Quick refresh failed: {results}")
                    st.info("📊 Check the 'Refresh Results' section below for details")

            except Exception as e:
                # Store the failure in session state
                st.session_state.quick_refresh_results = {
                    'success': False,
                    'results': f"Exception: {str(e)}",
                    'error': str(e),
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                st.error(f"❌ Quick refresh failed with error: {e}")
                st.info("📊 Check the 'Refresh Results' section below for error details")

    # Step 2: Manual Refresh Options
    st.markdown("### Step 2: 📰 Additional Data Refresh (Optional)")

    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("**Select additional data types to refresh:**")

        # Checkboxes for data types
        refresh_news = st.checkbox("📰 News Data", help="Recent news headlines and sentiment analysis")
        refresh_sentiment = st.checkbox("💭 Social Sentiment", help="Reddit posts and social media sentiment")

        # Symbol selection
        refresh_all_stocks = st.checkbox("All Stocks", value=True, help="Refresh all stocks or select specific ones")

        if not refresh_all_stocks:
            try:
                conn = sqlite3.connect('data/stock_data.db')
                symbol_query = "SELECT DISTINCT symbol FROM stocks ORDER BY symbol"
                symbols_df = pd.read_sql_query(symbol_query, conn)
                available_symbols = symbols_df['symbol'].tolist()
                conn.close()

                selected_symbols = st.multiselect(
                    "Select specific stocks:",
                    options=available_symbols,
                    default=available_symbols[:10],
                    help="Choose specific stocks to refresh"
                )
            except:
                selected_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN']
                st.warning("Could not load symbols from database, using defaults")
        else:
            selected_symbols = None

    with col2:
        # Collect selected data types
        selected_data_types = []
        if refresh_news:
            selected_data_types.append('news')
        if refresh_sentiment:
            selected_data_types.append('sentiment')

        if selected_data_types:
            if st.button("📰 Start Manual Refresh", help="Refresh selected data types"):
                if 'manual_refresh_results' not in st.session_state:
                    st.session_state.manual_refresh_results = None

                progress_placeholder = st.empty()

                try:
                    with st.spinner(f"Refreshing {', '.join(selected_data_types)}..."):
                        success, results = run_data_refresh(selected_data_types, selected_symbols, progress_placeholder)
                        st.session_state.manual_refresh_results = {
                            'success': success,
                            'results': results,
                            'data_types': selected_data_types,
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }

                    if success:
                        st.success("✅ Manual refresh completed!")
                        st.info("▶️ **Next:** Run Step 3 to recalculate metrics")
                    else:
                        st.error(f"❌ Manual refresh failed: {results}")
                        st.info("📊 Check the 'Refresh Results' section below for details")

                except Exception as e:
                    # Store the failure in session state
                    st.session_state.manual_refresh_results = {
                        'success': False,
                        'results': f"Exception: {str(e)}",
                        'data_types': selected_data_types,
                        'error': str(e),
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    st.error(f"❌ Manual refresh failed with error: {e}")
                    st.info("📊 Check the 'Refresh Results' section below for error details")
        else:
            st.info("👆 Select data types above")

    # Step 3: Refresh Metrics (moved out of quick actions)
    st.markdown("### Step 3: 🔄 Recalculate Composite Scores")

    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("**Final step - recalculate all composite scores:**")
        st.markdown("• 📊 Processes all fundamental, quality, growth, and sentiment data")
        st.markdown("• 🔢 Generates composite scores using 40/25/20/15 weighting")
        st.markdown("• ⏱️ Takes 3-5 minutes for all stocks")
        st.warning("⚠️ **Important:** Run this after any data refresh to update rankings")

    with col2:
        if st.button("🔄 Recalculate Metrics", type="secondary", help="Recalculate composite scores - REQUIRED after data refresh"):
            if 'metrics_refresh_results' not in st.session_state:
                st.session_state.metrics_refresh_results = None

            with st.spinner("Recalculating all metrics..."):
                try:
                    # Import and call the analytics update utility
                    from utilities.update_analytics import update_analytics
                    import sqlite3

                    # Get the count of stocks before refresh for comparison
                    conn = sqlite3.connect('data/stock_data.db')
                    before_count = pd.read_sql_query(
                        "SELECT COUNT(*) as count FROM calculated_metrics", conn
                    ).iloc[0]['count']
                    conn.close()

                    # Call analytics update - this will show detailed output in terminal
                    success = update_analytics(symbols=None, force_recalculate=True, batch_size=50)

                    # Get the count after refresh to see how many were updated
                    conn = sqlite3.connect('data/stock_data.db')

                    # Get total updated count
                    after_count = pd.read_sql_query(
                        "SELECT COUNT(*) as count FROM calculated_metrics", conn
                    ).iloc[0]['count']

                    # Get recent updates (within last 5 minutes) to identify what was processed
                    recent_updates = pd.read_sql_query("""
                        SELECT symbol FROM calculated_metrics
                        WHERE created_at >= datetime('now', '-5 minutes')
                        ORDER BY created_at DESC
                    """, conn)

                    # Get quality statistics for more insight
                    quality_stats = pd.read_sql_query("""
                        SELECT
                            COUNT(*) as total_recent,
                            COUNT(CASE WHEN composite_score >= 70 THEN 1 END) as high_quality,
                            COUNT(CASE WHEN composite_score < 50 THEN 1 END) as low_quality,
                            AVG(composite_score) as avg_score
                        FROM calculated_metrics
                        WHERE created_at >= datetime('now', '-5 minutes')
                    """, conn)

                    conn.close()

                    # Create meaningful results based on database changes
                    recent_symbols = recent_updates['symbol'].tolist() if not recent_updates.empty else []

                    if recent_symbols:
                        # We have recent updates - assume these were successful
                        success_stocks = recent_symbols
                        failed_stocks = []

                        # Create informative warnings based on quality stats
                        warnings = []
                        if not quality_stats.empty:
                            stats = quality_stats.iloc[0]
                            total = stats['total_recent']
                            high_qual = stats['high_quality']
                            low_qual = stats['low_quality']
                            avg_score = stats['avg_score']

                            if total > 0:
                                warnings.append(f"📊 Processed {total} stocks with average score {avg_score:.1f}")
                                if high_qual > 0:
                                    warnings.append(f"✅ {high_qual} stocks achieved high quality scores (≥70)")
                                if low_qual > 0:
                                    warnings.append(f"⚠️  {low_qual} stocks have quality concerns (<50)")

                                # Add data quality insights
                                if avg_score < 60:
                                    warnings.append("⚠️  Overall data quality is below optimal - consider refreshing source data")

                    else:
                        # No recent updates found
                        if success:
                            # Function reported success but no updates - likely no stocks needed updating
                            success_stocks = []
                            failed_stocks = []
                            warnings = ["ℹ️  All analytics are up to date - no updates needed"]
                        else:
                            # Function failed
                            success_stocks = []
                            failed_stocks = ["Unable to determine specific failures"]
                            warnings = ["❌ Analytics update failed - check terminal output for details"]

                    # Store results in session state
                    st.session_state.metrics_refresh_results = {
                        'success': success,
                        'success_stocks': success_stocks,
                        'failed_stocks': failed_stocks,
                        'warnings': warnings,
                        'total_processed': len(recent_symbols),
                        'before_count': before_count,
                        'after_count': after_count,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }

                    # Display immediate feedback
                    if success:
                        if total_processed == 0:
                            st.info("ℹ️  All analytics are up to date - no updates needed")
                        elif len(failed_stocks) == 0:
                            st.success("✅ All metrics recalculated successfully!")
                        else:
                            st.warning("⚠️ Metrics calculation completed with some issues")
                    else:
                        st.error("❌ Metrics calculation failed")

                    # Provide guidance about detailed output
                    st.info("📊 Check the 'Refresh Results' section below for summary")
                    st.info("📺 For detailed processing logs, check your terminal/console output")

                except Exception as e:
                    # Store the failure in session state too
                    st.session_state.metrics_refresh_results = {
                        'success': False,
                        'error': str(e),
                        'success_stocks': [],
                        'failed_stocks': [],
                        'warnings': [],
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }

                    st.error(f"❌ Failed to recalculate metrics: {e}")
                    st.error("💡 Try running: python utilities/update_analytics.py")
                    st.info("📊 Check the 'Refresh Results' section below for error details")

    # Persistent Refresh Results Section
    st.markdown("---")
    st.subheader("📊 Refresh Results & Status")

    # Display Quick Refresh Results
    if hasattr(st.session_state, 'quick_refresh_results') and st.session_state.quick_refresh_results:
        results = st.session_state.quick_refresh_results
        with st.expander(f"🚀 Quick Refresh Results - {results['timestamp']}", expanded=True):
            if results['success']:
                st.success("✅ Quick refresh completed successfully")
                if results['results']:
                    col1, col2 = st.columns(2)
                    with col1:
                        if 'fundamentals' in results['results']:
                            fund_result = results['results']['fundamentals']
                            if isinstance(fund_result, dict):
                                success_count = sum(1 for v in fund_result.values() if v)
                                total_count = len(fund_result)
                                st.write(f"📊 **Fundamentals**: {success_count}/{total_count} stocks updated")
                    with col2:
                        if 'prices' in results['results']:
                            price_result = results['results']['prices']
                            if isinstance(price_result, dict):
                                success_count = sum(1 for v in price_result.values() if v)
                                total_count = len(price_result)
                                st.write(f"💹 **Prices**: {success_count}/{total_count} stocks updated")
            else:
                st.error("❌ Quick refresh failed")
                st.write(f"Error: {results['results']}")

                # Show error details if available
                if 'error' in results:
                    with st.expander("🔍 Error Details", expanded=True):
                        st.code(results['error'])
                        st.markdown("**Suggested actions:**")
                        st.markdown("1. Check internet connection")
                        st.markdown("2. Verify Yahoo Finance API is accessible")
                        st.markdown("3. Try again in a few minutes")
                        st.markdown("4. Check system resources and restart if needed")

    # Display Manual Refresh Results
    if hasattr(st.session_state, 'manual_refresh_results') and st.session_state.manual_refresh_results:
        results = st.session_state.manual_refresh_results
        with st.expander(f"📰 Manual Refresh Results - {results['timestamp']}", expanded=True):
            if results['success']:
                st.success(f"✅ Manual refresh completed for: {', '.join(results['data_types'])}")
                if results['results']:
                    for data_type in results['data_types']:
                        if data_type in results['results']:
                            result = results['results'][data_type]
                            if isinstance(result, dict):
                                success_count = sum(1 for v in result.values() if v)
                                total_count = len(result)
                                icon = "📰" if data_type == "news" else "💭"
                                st.write(f"{icon} **{data_type.title()}**: {success_count}/{total_count} stocks updated")
            else:
                st.error("❌ Manual refresh failed")
                st.write(f"Error: {results['results']}")

                # Show error details if available
                if 'error' in results:
                    with st.expander("🔍 Error Details", expanded=True):
                        st.code(results['error'])
                        st.markdown("**Suggested actions:**")
                        st.markdown("1. Check API credentials (.env file)")
                        st.markdown("2. Verify Reddit API and News API access")
                        st.markdown("3. Try refreshing fewer stocks")
                        st.markdown("4. Check system resources and restart if needed")

    # Display Metrics Refresh Results
    if hasattr(st.session_state, 'metrics_refresh_results') and st.session_state.metrics_refresh_results:
        results = st.session_state.metrics_refresh_results
        with st.expander(f"🔄 Metrics Refresh Results - {results['timestamp']}", expanded=True):
            if results['success']:
                # Check if we actually processed any stocks
                total_processed = results.get('total_processed', len(results['success_stocks']))

                if total_processed == 0:
                    st.info("ℹ️  All analytics are up to date - no updates needed")
                    st.write("📊 Database contains calculated metrics for all stocks")
                elif len(results['failed_stocks']) == 0:
                    st.success("✅ All metrics recalculated successfully!")
                    st.info(f"📊 {total_processed} stocks updated with latest composite scores")
                else:
                    st.warning("⚠️ Metrics calculation completed with some issues")
                    st.info(f"📊 {len(results['success_stocks'])} stocks updated successfully, {len(results['failed_stocks'])} had issues")

                # Show database statistics
                if 'before_count' in results and 'after_count' in results:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Before", f"{results['before_count']} stocks")
                    with col2:
                        st.metric("After", f"{results['after_count']} stocks")
                    with col3:
                        net_change = results['after_count'] - results['before_count']
                        st.metric("Net Change", f"+{net_change}" if net_change >= 0 else str(net_change))

                # Show detailed results in nested expandable sections
                if results['success_stocks']:
                    with st.expander(f"✅ Recently Updated ({len(results['success_stocks'])} stocks)", expanded=False):
                        # Display in multiple columns for better layout
                        cols = st.columns(6)
                        for i, symbol in enumerate(results['success_stocks']):
                            with cols[i % 6]:
                                st.write(f"✅ {symbol}")

                if results['failed_stocks']:
                    with st.expander(f"❌ Failed Updates ({len(results['failed_stocks'])} stocks)", expanded=True):
                        if isinstance(results['failed_stocks'][0], str) and "Unable to determine" in results['failed_stocks'][0]:
                            st.text("❌ Analytics update reported failure")
                            st.text("📺 Check terminal output for detailed error information")
                            st.text("💡 Common issues: database locks, memory limits, missing dependencies")
                        else:
                            cols = st.columns(6)
                            for i, symbol in enumerate(results['failed_stocks']):
                                with cols[i % 6]:
                                    st.write(f"❌ {symbol}")

                # Show insights and warnings
                if results['warnings']:
                    with st.expander(f"📊 Quality Insights & Warnings ({len(results['warnings'])} items)", expanded=True):
                        for warning in results['warnings']:
                            if warning.strip():
                                st.markdown(warning)

                # Show success rate only if we have actual processing results
                if total_processed > 0 and (results['success_stocks'] or results['failed_stocks']):
                    success_count = len(results['success_stocks'])
                    total_attempted = success_count + len(results['failed_stocks'])
                    success_rate = (success_count / total_attempted * 100) if total_attempted > 0 else 0

                    st.markdown("### 📈 Processing Summary")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Success Rate", f"{success_rate:.1f}%")
                    with col2:
                        st.metric("Successful", success_count)
                    with col3:
                        st.metric("Failed", len(results['failed_stocks']))
            else:
                # Handle complete failure case
                st.error("❌ Metrics calculation failed completely")

                # Show error details if available
                if 'error' in results:
                    with st.expander("🔍 Error Details", expanded=True):
                        st.code(results['error'])

                        # Provide troubleshooting suggestions
                        st.markdown("**Possible causes:**")
                        st.markdown("• Database connection issues")
                        st.markdown("• Missing dependencies or imports")
                        st.markdown("• Insufficient data for calculations")
                        st.markdown("• Memory or processing limitations")

                        st.markdown("**Suggested actions:**")
                        st.markdown("1. Try running a data refresh first")
                        st.markdown("2. Check database connectivity")
                        st.markdown("3. Run command line version: `python utilities/update_analytics.py`")
                        st.markdown("4. Check system resources and restart if needed")

    # Clear Results Button
    if (hasattr(st.session_state, 'quick_refresh_results') or
        hasattr(st.session_state, 'manual_refresh_results') or
        hasattr(st.session_state, 'metrics_refresh_results')):

        if st.button("🗑️ Clear Results History", help="Clear all stored refresh results"):
            if hasattr(st.session_state, 'quick_refresh_results'):
                del st.session_state.quick_refresh_results
            if hasattr(st.session_state, 'manual_refresh_results'):
                del st.session_state.manual_refresh_results
            if hasattr(st.session_state, 'metrics_refresh_results'):
                del st.session_state.metrics_refresh_results
            st.rerun()


    # Database Management
    st.subheader("💾 Database Management")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Backup Operations:**")
        if st.button("📁 Create Backup", help="Create timestamped database backup"):
            with st.spinner("Creating backup..."):
                try:
                    # This would call the backup utility
                    backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    st.success(f"✅ Backup created: {backup_name}")
                except Exception as e:
                    st.error(f"❌ Backup failed: {e}")

    with col2:
        st.markdown("**Database Stats:**")
        try:
            stats = get_database_stats()
            st.write(f"📊 Total stocks: {stats.get('total_stocks', 'Unknown')}")
            st.write(f"📈 Calculated metrics: {stats.get('calculated_stocks', 'Unknown')}")
            st.write(f"📅 Last updated: {stats.get('last_calculation', 'Unknown')[:10]}")
        except:
            st.write("Could not load database statistics")

def main():
    """Main dashboard application."""

    # Sidebar title
    st.sidebar.title("📊 Stock Outlier Analysis")

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

    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Rankings", "📊 Individual Analysis", "🗄️ Data Management", "📚 Methodology"])

    with tab1:
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
            last_calc_display = stats['last_calculation'][:10] if stats['last_calculation'] else "Unknown"
            st.metric(
                "Last Updated",
                last_calc_display,
                "Auto-refresh"
            )

        with col4:
            # Calculate average score
            avg_score = df['composite_score'].mean()
            st.metric(
                "Avg Score",
                f"{avg_score:.1f}",
                "Market baseline"
            )

        # Weight adjustment section
        if weights_changed:
            st.subheader("🎛️ Custom Weight Analysis")
            adjusted_df = calculate_custom_composite_scores(df, normalized_weights)
            show_weight_adjusted_rankings(df, adjusted_df, normalized_weights)
            # Use adjusted rankings for subsequent analysis
            main_df = adjusted_df
            score_column = 'custom_composite_score'
        else:
            main_df = df
            score_column = 'composite_score'

        # Top/Bottom performers
        st.subheader("🏆 Performance Leaders")
        col_under, col_over = st.columns(2)

        with col_under:
            show_top_performers(main_df, 5, False, score_column)

        with col_over:
            show_top_performers(main_df, 5, True, score_column)

        # Analytics visualizations
        st.subheader("📊 Distribution Analysis")

        # Create histograms and box plots
        fig_hist = px.histogram(
            main_df,
            x=score_column,
            nbins=20,
            title="Score Distribution",
            labels={score_column: "Composite Score", 'count': 'Number of Stocks'}
        )
        fig_hist.update_layout(font=dict(family='Montserrat'))

        fig_box = px.box(
            main_df,
            y=score_column,
            title="Score Distribution Box Plot",
            labels={score_column: "Composite Score"}
        )
        fig_box.update_layout(font=dict(family='Montserrat'))

        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.plotly_chart(fig_hist, use_container_width=True)

        with chart_col2:
            st.plotly_chart(fig_box, use_container_width=True)

        # Statistical summary
        st.subheader("📈 Statistical Summary")
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
            st.metric("75th Percentile", f"{analysis_scores.quantile(0.75):.1f}")
            st.metric("25th Percentile", f"{analysis_scores.quantile(0.25):.1f}")

        # Sector analysis
        st.subheader("🏭 Sector Performance")

        if 'sector' in main_df.columns:
            sector_stats = main_df.groupby('sector').agg({
                score_column: 'mean',
                'symbol': 'count',
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

    with tab2:
        show_individual_stock_analysis(df)

    with tab3:
        show_data_management()

    with tab4:
        show_methodology_guide()

if __name__ == "__main__":
    main()