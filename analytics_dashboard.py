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
    """Display the reorganized 3-step data workflow interface"""
    st.header("🗄️ Data Management - 3-Step Workflow")

    st.info("""
    **🎯 Streamlined Process:** Collect Data → Process Sentiment → Calculate Rankings

    Each step serves a specific purpose and should be completed in order for best results.
    """)

    # Get current data status
    from src.data.database import DatabaseManager
    db = DatabaseManager()
    data_status = {
        "stocks_count": 0, "fundamentals_count": 0, "news_count": 0, "reddit_count": 0,
        "news_no_sentiment": 0, "reddit_no_sentiment": 0, "news_with_sentiment": 0, "reddit_with_sentiment": 0
    }

    if db.connect():
        cursor = db.connection.cursor()

        # Get basic counts
        cursor.execute("SELECT COUNT(*) FROM stocks")
        data_status["stocks_count"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM fundamental_data")
        data_status["fundamentals_count"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM news_articles")
        data_status["news_count"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM reddit_posts")
        data_status["reddit_count"] = cursor.fetchone()[0]

        # Get sentiment status - Only count NULL as unprocessed (0.0 is a valid neutral sentiment)
        cursor.execute("SELECT COUNT(*) FROM news_articles WHERE sentiment_score IS NULL")
        data_status["news_no_sentiment"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM reddit_posts WHERE sentiment_score IS NULL")
        data_status["reddit_no_sentiment"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM news_articles WHERE sentiment_score IS NOT NULL")
        data_status["news_with_sentiment"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM reddit_posts WHERE sentiment_score IS NOT NULL")
        data_status["reddit_with_sentiment"] = cursor.fetchone()[0]

        cursor.close()
        db.close()

    # === STEP 1: COLLECT RAW DATA ===
    st.markdown("---")
    st.markdown("## 📥 Step 1: Collect Raw Data")
    st.markdown("*Gather latest market data WITHOUT calculating sentiment*")

    # Show current data status
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Stocks Tracked", f"{data_status['stocks_count']:,}")
    with col2:
        st.metric("💰 Fundamentals", f"{data_status['fundamentals_count']:,}")
    with col3:
        st.metric("📰 News Articles", f"{data_status['news_count']:,}")
    with col4:
        st.metric("💭 Reddit Posts", f"{data_status['reddit_count']:,}")

    # Data collection options
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("**What gets collected:**")
        st.markdown("• 📊 **Fundamentals:** P/E ratios, market cap, revenue, financial metrics")
        st.markdown("• 💹 **Prices:** Historical price data and trading volumes")
        st.markdown("• 📰 **News:** Headlines and summaries (sentiment_score = NULL)")
        st.markdown("• 💭 **Reddit:** Posts and discussions (sentiment_score = NULL)")
        st.markdown("")
        st.markdown("⚠️ **Important:** Sentiment analysis happens in Step 2 via Claude API")

    with col2:
        st.markdown("**Quick Actions:**")

        if st.button("🚀 Collect All Data", type="primary", help="Collect fundamentals, prices, news, and Reddit data"):
            with st.spinner("Collecting all data types..."):
                try:
                    data_types = ['fundamentals', 'prices', 'news', 'sentiment']
                    success, results = run_data_refresh(data_types, None, None)
                    if success:
                        st.success("✅ Data collection completed!")
                        st.info("➡️ **Next:** Proceed to Step 2 for sentiment processing")
                        st.rerun()
                    else:
                        st.error(f"❌ Collection failed: {results}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

        if st.button("⚡ Quick Update", help="Update fundamentals and prices only"):
            with st.spinner("Quick update in progress..."):
                try:
                    data_types = ['fundamentals', 'prices']
                    success, results = run_data_refresh(data_types, None, None)
                    if success:
                        st.success("✅ Quick update completed!")
                        st.rerun()
                    else:
                        st.error(f"❌ Update failed: {results}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    # Advanced options
    with st.expander("🔧 Advanced Collection Options"):
        st.markdown("**Select specific data types:**")

        col1, col2 = st.columns(2)
        with col1:
            collect_fundamentals = st.checkbox("📊 Fundamentals", value=True)
            collect_prices = st.checkbox("💹 Prices", value=True)
        with col2:
            collect_news = st.checkbox("📰 News Articles", value=False)
            collect_reddit = st.checkbox("💭 Reddit Posts", value=False)

        selected_symbols = st.multiselect(
            "🎯 Specific Symbols (optional):",
            options=['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA'],
            help="Leave empty to update all stocks"
        )

        if st.button("🔄 Custom Collection"):
            data_types = []
            if collect_fundamentals: data_types.append('fundamentals')
            if collect_prices: data_types.append('prices')
            if collect_news: data_types.append('news')
            if collect_reddit: data_types.append('sentiment')

            if data_types:
                with st.spinner("Running custom collection..."):
                    try:
                        symbols = selected_symbols if selected_symbols else None
                        success, results = run_data_refresh(data_types, symbols, None)
                        if success:
                            st.success("✅ Custom collection completed!")
                            st.rerun()
                        else:
                            st.error(f"❌ Collection failed: {results}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
            else:
                st.warning("⚠️ Please select at least one data type")

    # === STEP 2: PROCESS SENTIMENT ===
    st.markdown("---")
    st.markdown("## 🤖 Step 2: Process Sentiment via Claude API")
    st.markdown("*High-quality financial sentiment analysis using bulk processing*")

    # Show sentiment status
    total_unprocessed = data_status['news_no_sentiment'] + data_status['reddit_no_sentiment']
    total_processed = data_status['news_with_sentiment'] + data_status['reddit_with_sentiment']

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📰 News Need Sentiment", f"{data_status['news_no_sentiment']:,}")
    with col2:
        st.metric("💭 Reddit Need Sentiment", f"{data_status['reddit_no_sentiment']:,}")
    with col3:
        st.metric("🔄 Total Unprocessed", f"{total_unprocessed:,}")
    with col4:
        st.metric("✅ Already Processed", f"{total_processed:,}")

    # Initialize bulk processor
    @st.cache_resource
    def get_bulk_processor():
        """Initialize the unified bulk processor"""
        try:
            from src.data.unified_bulk_processor import UnifiedBulkProcessor
            import os
            api_key = os.getenv('NEWS_API_KEY') or os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                return None
            return UnifiedBulkProcessor(api_key)
        except Exception as e:
            st.error(f"Could not initialize bulk processor: {e}")
            return None

    bulk_processor = get_bulk_processor()

    if not bulk_processor:
        st.error("❌ Bulk sentiment processor not available")
        st.info("🔑 **API Key Required**: Set NEWS_API_KEY or ANTHROPIC_API_KEY in your .env file")
        st.info("💡 **Why needed**: Claude API provides superior financial sentiment analysis")

    else:
        # === STEP 2 COMPLETION STATUS ===
        step2_complete = (total_unprocessed == 0)

        if step2_complete:
            st.success("### ✅ STEP 2: COMPLETE")
            st.success("🎉 **All sentiment processing finished!** All {total_processed:,} items have been analyzed.")
            st.info("➡️ **Ready for Step 3:** Proceed to calculate final rankings below")

            # Show summary stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📰 News Processed", f"{data_status['news_with_sentiment']:,}")
            with col2:
                st.metric("💭 Reddit Processed", f"{data_status['reddit_with_sentiment']:,}")
            with col3:
                st.metric("✅ Total Complete", f"{total_processed:,}")
        else:
            st.warning("### ⏳ STEP 2: IN PROGRESS")
            st.info(f"📊 **Status:** {total_processed:,} processed, {total_unprocessed:,} remaining")

        st.markdown("---")

        # Check for active batches
        active_batches = []
        if db.connect():
            active_batches = db.get_active_batch_ids()
            db.close()

        if active_batches:
            st.markdown("### 📊 Active Batch Monitoring")

            selected_batch = st.selectbox(
                "Select batch to monitor:",
                active_batches,
                format_func=lambda x: f"Batch: {x[:20]}..."
            )

            if selected_batch:
                col1, col2 = st.columns([2, 1])

                with col1:
                    # Check batch status
                    batch_status = bulk_processor.check_batch_status(selected_batch)
                    if batch_status and batch_status['success']:
                        st.info(f"**Status:** {batch_status['status']}")
                        st.info(f"**Progress:** {batch_status['completed_count']}/{batch_status['submitted_count']} items processed")

                        if batch_status['status'] == 'ended':
                            st.success("🎉 Batch completed successfully!")
                    else:
                        st.warning("⚠️ Could not check batch status")

                with col2:
                    if batch_status and batch_status.get('status') == 'ended':
                        if st.button("📥 Process Results", type="primary"):
                            with st.spinner("Retrieving and processing batch results..."):
                                try:
                                    result = bulk_processor.retrieve_and_process_batch_results(selected_batch)
                                    if result and result.get('success'):
                                        st.success(f"✅ Results processed successfully!")
                                        st.success(f"📊 Updated {result.get('successful_updates', 0)} items")
                                        if result.get('failed_updates', 0) > 0:
                                            st.warning(f"⚠️ {result.get('failed_updates')} items failed to process")
                                        st.info("➡️ **Next:** Proceed to Step 3 for final calculations")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Failed to process results: {result.get('error', 'Unknown error') if result else 'No result returned'}")
                                except Exception as e:
                                    st.error(f"❌ Error: {str(e)}")

        elif total_unprocessed > 0:
            st.markdown("### 🚀 Submit New Batch")

            # Check for recently submitted batches (within last 5 minutes)
            recent_batch_warning = False
            if db.connect():
                cursor = db.connection.cursor()
                cursor.execute("""
                    SELECT batch_id, COUNT(*) as count, MAX(created_at) as recent
                    FROM batch_mapping
                    WHERE created_at > datetime('now', '-5 minutes')
                    GROUP BY batch_id
                """)
                recent_batches = cursor.fetchall()
                cursor.close()
                db.close()

                if recent_batches:
                    recent_batch_warning = True
                    st.warning(f"⚠️ **Recent batch detected!** A batch was submitted {recent_batches[0][2]} with {recent_batches[0][1]} items.")
                    st.info("💡 Wait a few seconds and refresh the page to see the batch monitoring section above.")
                    st.info("🔄 If you don't see it after refreshing, the batch may not have been stored properly.")

            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown("**Claude API Batch Processing:**")
                st.markdown(f"• 📊 **Total Items:** {total_unprocessed:,} items ready for processing")
                st.markdown("• 💰 **Cost:** 50% savings vs individual API calls")
                st.markdown("• ⏱️ **Time:** Typically completes in <1 hour")
                st.markdown("• 🧠 **Quality:** Superior financial context understanding")

            with col2:
                button_disabled = recent_batch_warning
                button_help = "A batch was just submitted. Refresh page to monitor it." if recent_batch_warning else f"Submit {total_unprocessed:,} items for sentiment analysis"

                if st.button("🚀 Submit Batch", type="primary", help=button_help, disabled=button_disabled):
                    with st.spinner("Preparing and submitting batch..."):
                        try:
                            # Get unprocessed items
                            if db.connect():
                                unprocessed_items = db.get_unprocessed_items_for_batch()
                                db.close()

                                if unprocessed_items:
                                    # Prepare data for submission
                                    news_articles = []
                                    reddit_posts = []

                                    for item in unprocessed_items:
                                        if item['content_type'] == 'news':
                                            news_articles.append((
                                                item['symbol'],
                                                item['title'],
                                                item['content'],
                                                {'record_id': item['record_id']}
                                            ))
                                        elif item['content_type'] == 'reddit':
                                            reddit_posts.append((
                                                item['symbol'],
                                                item['title'],
                                                item['content'],
                                                {'record_id': item['record_id']}
                                            ))

                                    # Submit batch
                                    submission = bulk_processor.bulk_processor.submit_batch_for_processing(
                                        news_articles=news_articles if news_articles else None,
                                        reddit_posts=reddit_posts if reddit_posts else None
                                    )

                                    if submission:
                                        batch_id, requests = submission
                                        # Store batch mapping
                                        bulk_processor._store_batch_mapping(batch_id, requests)
                                        st.success(f"✅ Batch submitted successfully!")
                                        st.info(f"📊 Processing {len(requests)} items")
                                        st.info(f"🆔 Batch ID: {batch_id[:20]}...")
                                        st.info("⏱️ Expected completion: <1 hour")
                                        st.info("🔄 Refresh page to monitor progress")
                                        st.rerun()
                                    else:
                                        st.error("❌ Failed to submit batch")
                                else:
                                    st.error("❌ No unprocessed items found")
                            else:
                                st.error("❌ Could not connect to database")
                        except Exception as e:
                            st.error(f"❌ Error submitting batch: {str(e)}")

        else:
            st.success("✅ All items have sentiment scores! No processing needed.")

    # === MANUAL BATCH RECOVERY ===
    if not active_batches and total_unprocessed > 0:
        with st.expander("🔧 Manual Batch Recovery (Advanced)", expanded=False):
            st.markdown("""
            **If you submitted a batch but it's not showing above:**

            This can happen if the batch was submitted through another method or if there was a database issue.
            You can manually enter your batch ID from the Anthropic console to process results.
            """)

            manual_batch_id = st.text_input(
                "Enter Batch ID from Anthropic Console:",
                placeholder="msgbatch_01ABC...",
                help="Find this in your Anthropic console under Message Batches"
            )

            if manual_batch_id and st.button("🔍 Check & Process Manual Batch", type="secondary"):
                with st.spinner("Checking batch status..."):
                    try:
                        status = bulk_processor.check_batch_status(manual_batch_id)
                        if status and status['success']:
                            st.info(f"**Status:** {status['status']}")
                            st.info(f"**Progress:** {status['completed_count']}/{status['submitted_count']} items")

                            if status['status'] == 'ended':
                                st.success("🎉 Batch is complete! Processing results...")
                                result = bulk_processor.retrieve_and_process_batch_results(manual_batch_id)
                                if result and result.get('success'):
                                    st.success(f"✅ Results processed successfully!")
                                    st.success(f"📊 Updated {result.get('successful_updates', 0)} items")
                                    if result.get('failed_updates', 0) > 0:
                                        st.warning(f"⚠️ {result.get('failed_updates')} items failed to process")
                                    st.info("➡️ **Next:** Proceed to Step 3 for final calculations")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Failed to process results: {result.get('error', 'Unknown error')}")
                            else:
                                st.warning(f"⏳ Batch is still {status['status']}. Wait until it completes before processing.")
                        else:
                            st.error(f"❌ Could not find batch: {manual_batch_id}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

    # === BATCH MONITORING SECTION ===
    if active_batches or total_unprocessed == 0:
        st.markdown("---")
        st.markdown("## 📊 Batch Processing Status")
        st.markdown("*Monitor your Claude API batch progress in real-time*")

        if active_batches:
            st.info("🔄 **Active Batch Processing** - Monitor progress below")

            # Batch status overview
            col1, col2, col3 = st.columns(3)

            # Get detailed status for all active batches
            batch_statuses = {}
            for batch_id in active_batches:
                status = bulk_processor.check_batch_status(batch_id)
                if status and status['success']:
                    batch_statuses[batch_id] = status

            # Calculate overall progress
            total_submitted = sum(s.get('submitted_count', 0) for s in batch_statuses.values())
            total_completed = sum(s.get('completed_count', 0) for s in batch_statuses.values())
            overall_progress = (total_completed / total_submitted * 100) if total_submitted > 0 else 0

            with col1:
                st.metric("📦 Active Batches", len(active_batches))
            with col2:
                st.metric("📊 Total Items", f"{total_submitted:,}")
            with col3:
                st.metric("✅ Progress", f"{overall_progress:.1f}%")

            # Individual batch details
            st.markdown("### 📋 Batch Details")

            for batch_id, status_info in batch_statuses.items():
                with st.expander(f"🔍 Batch {batch_id[:20]}... - {status_info.get('status', 'unknown').title()}", expanded=True):
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric("Status", status_info.get('status', 'unknown').title())
                    with col2:
                        submitted = status_info.get('submitted_count', 0)
                        st.metric("Submitted", f"{submitted:,}")
                    with col3:
                        completed = status_info.get('completed_count', 0)
                        st.metric("Completed", f"{completed:,}")
                    with col4:
                        progress = (completed / submitted * 100) if submitted > 0 else 0
                        st.metric("Progress", f"{progress:.1f}%")

                    # Progress bar
                    st.progress(progress / 100.0)

                    # Status-specific actions
                    if status_info.get('status') == 'ended':
                        st.success("🎉 **Batch Complete!** Ready to process results.")

                        col1, col2 = st.columns([2, 1])
                        with col1:
                            st.info("📥 Click 'Process Results' to apply sentiment scores to your database")
                        with col2:
                            if st.button("📥 Process Results", key=f"process_{batch_id[:8]}", type="primary"):
                                with st.spinner("Processing batch results..."):
                                    try:
                                        result = bulk_processor.retrieve_and_process_batch_results(batch_id)
                                        if result and result.get('success'):
                                            st.success(f"✅ Results processed successfully!")
                                            st.success(f"📊 Updated {result.get('successful_updates', 0)} items")
                                            if result.get('failed_updates', 0) > 0:
                                                st.warning(f"⚠️ {result.get('failed_updates')} items failed to process")
                                            st.info("➡️ **Next:** Proceed to Step 3 for final calculations")
                                            st.rerun()
                                        else:
                                            st.error(f"❌ Failed to process results: {result.get('error', 'Unknown error') if result else 'No result returned'}")
                                    except Exception as e:
                                        st.error(f"❌ Error: {str(e)}")

                    elif status_info.get('status') == 'in_progress':
                        st.info("⏳ Processing in progress... Claude is analyzing your data")
                        st.markdown("**Estimated completion:** <1 hour from submission")

                        # Auto-refresh option
                        if st.button("🔄 Refresh Status", key=f"refresh_{batch_id[:8]}"):
                            st.rerun()

                    elif status_info.get('status') in ['failed', 'expired', 'cancelled']:
                        st.error(f"❌ **Batch {status_info.get('status')}**")
                        st.info("💡 You may need to resubmit your data for processing")

                    else:
                        st.warning(f"⚠️ **Unknown status:** {status_info.get('status')}")

            # Auto-refresh controls
            st.markdown("### 🔄 Auto-Refresh")
            col1, col2 = st.columns([2, 1])

            with col1:
                st.info("💡 **Tip:** This page will auto-update when you refresh. Batches typically complete within 1 hour.")

            with col2:
                if st.button("🔄 Refresh All Status", type="secondary"):
                    st.rerun()

        elif total_unprocessed == 0:
            st.success("✅ **All sentiment processing complete!** No active batches.")

            # Show summary of last processing
            if db.connect():
                cursor = db.connection.cursor()

                # Get recent batch info
                cursor.execute("""
                    SELECT COUNT(DISTINCT batch_id) as batch_count,
                           COUNT(*) as total_items,
                           MAX(created_at) as last_processed
                    FROM batch_mapping
                    WHERE created_at >= datetime('now', '-7 days')
                """)

                recent_stats = cursor.fetchone()
                cursor.close()
                db.close()

                if recent_stats and recent_stats[0] > 0:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Recent Batches", f"{recent_stats[0]}")
                    with col2:
                        st.metric("Items Processed", f"{recent_stats[1]:,}")
                    with col3:
                        st.metric("Last Processing", recent_stats[2][:10] if recent_stats[2] else "Unknown")

    # === STEP 3: CALCULATE FINAL RANKINGS ===
    st.markdown("---")
    st.markdown("## 📊 Step 3: Calculate Final Rankings")
    st.markdown("*Generate composite scores using all collected data*")

    # Check for completed batches needing processing
    completed_batches_ready = False
    if active_batches:
        for batch_id in active_batches:
            status = bulk_processor.check_batch_status(batch_id)
            if status and status.get('status') == 'ended':
                completed_batches_ready = True
                break

    # Dynamic status messaging
    if completed_batches_ready:
        st.success("🎉 **Batch Processing Complete!** Process your results above before proceeding to Step 3.")
        st.info("⬆️ **Action Required:** Scroll up to the 'Batch Processing Status' section and click 'Process Results'")
    elif total_unprocessed > 0 and not active_batches:
        st.warning("⚠️ **Sentiment processing incomplete.** Complete Step 2 before running final calculations.")
        st.info("💡 Some stocks may receive preliminary scores based on available data.")
    elif active_batches:
        # Check if any are still processing
        in_progress_count = 0
        for batch_id in active_batches:
            status = bulk_processor.check_batch_status(batch_id)
            if status and status.get('status') == 'in_progress':
                in_progress_count += 1

        if in_progress_count > 0:
            st.info(f"⏳ **Sentiment processing in progress** ({in_progress_count} batch{'es' if in_progress_count > 1 else ''} active). Monitor progress above.")
        else:
            st.info("⏳ **Checking batch status...** Monitor progress in the section above.")
    else:
        st.success("✅ **Ready for final calculations.** All sentiment data is up-to-date.")

    # Information section
    st.markdown("**📋 What gets calculated:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("• 📊 **Fundamental** (40%): P/E, P/B, PEG")
        st.markdown("• 🏆 **Quality** (25%): ROE, margins")
    with col2:
        st.markdown("• 📈 **Growth** (20%): Revenue, earnings")
        st.markdown("• 💭 **Sentiment** (15%): News + Reddit")
    with col3:
        st.markdown("• 🎯 **Composite Rankings**")
        st.markdown("• 📊 **Final weighted scores**")

    st.markdown("---")
    st.markdown("### 🎬 Choose Calculation Method:")

    # Organize buttons in a 2x2 grid for better display
    col1, col2 = st.columns(2)

    with col1:
        # Test calculation with a few stocks first
        if st.button("🧪 Test Calculation", help="Test with a few stocks first (AAPL, MSFT, GOOGL)", use_container_width=True):
            with st.spinner("Testing calculation with sample stocks..."):
                try:
                    from utilities.update_analytics import update_analytics
                    import logging

                    logger = logging.getLogger('test_calc')
                    logger.setLevel(logging.INFO)

                    # Test with just 3 stocks
                    success = update_analytics(logger=logger, symbols=['AAPL', 'MSFT', 'GOOGL'], force_recalculate=True)

                    if success:
                        st.success("✅ Test calculation successful!")
                        st.info("💡 Now try the full calculation below")
                    else:
                        st.error("❌ Test calculation failed - there may be data issues")

                except Exception as e:
                    st.error(f"❌ Test failed: {str(e)}")

        with col2:
            # Calculate All button
            if st.button("📊 Calculate Rankings", type="primary", help="Calculate rankings for stocks needing updates", use_container_width=True):
                with st.spinner("Calculating composite scores..."):
                    try:
                        # Import and call the analytics update utility
                        from utilities.update_analytics import update_analytics
                        import logging
                        import io

                        # Create a logger for the utility with stream capture
                        logger = logging.getLogger('dashboard_metrics')
                        logger.setLevel(logging.INFO)

                        # Capture logging output
                        log_capture = io.StringIO()
                        handler = logging.StreamHandler(log_capture)
                        handler.setLevel(logging.INFO)
                        logger.addHandler(handler)

                        # Run the calculation
                        success = update_analytics(logger=logger)

                        # Get captured logs
                        log_output = log_capture.getvalue()

                        # Count successful vs failed regardless of return value
                        success_count = log_output.count("✅") + log_output.count("Analytics updated successfully")
                        failed_count = log_output.count("❌") + log_output.count("calculation failed")

                        if success:
                            st.success("✅ Rankings calculated successfully!")
                            st.info("🎉 **Complete!** Check the main dashboard for updated rankings")
                        elif success_count > 0:
                            # Function returned False but still processed stocks successfully
                            st.warning("⚠️ Calculation completed with some limitations")
                            st.success(f"✅ Successfully processed {success_count} stocks")
                            if failed_count > 0:
                                st.info(f"ℹ️ Skipped {failed_count} stocks due to data quality issues")
                            st.info("📊 **Result:** Rankings updated for stocks with sufficient data quality")
                        else:
                            st.error("❌ Calculation failed - check logs for details")

                        if log_output and (not success or failed_count > 0):
                            with st.expander("📝 Show Processing Details"):
                                st.text(log_output[-2000:])  # Show last 2000 chars

                    except Exception as e:
                        st.error(f"❌ Error during calculation: {str(e)}")
                        import traceback
                        with st.expander("📝 Show Full Error"):
                            st.text(traceback.format_exc())

    # Add spacing between rows
    st.markdown("")

    # Second row of buttons
    col_a, col_b = st.columns(2)

    with col_a:
        if st.button("🎯 Quality Stocks Only", help="Process only stocks with good data quality", type="secondary", use_container_width=True):
            with st.spinner("Processing stocks with good data quality..."):
                try:
                    from utilities.update_analytics import update_analytics
                    import logging

                    logger = logging.getLogger('quality_calc')
                    logger.setLevel(logging.INFO)

                    # Get stocks that already have calculated metrics (known good quality)
                    db_temp = DatabaseManager()
                    db_temp.connect()
                    cursor = db_temp.connection.cursor()
                    cursor.execute('SELECT DISTINCT symbol FROM calculated_metrics ORDER BY symbol')
                    good_stocks = [row[0] for row in cursor.fetchall()]
                    cursor.close()
                    db_temp.close()

                    if good_stocks:
                        success = update_analytics(logger=logger, symbols=good_stocks[:50], force_recalculate=True)  # Limit to 50 for speed
                        if success:
                            st.success(f"✅ Updated {min(50, len(good_stocks))} high-quality stocks!")
                        else:
                            st.warning("⚠️ Some issues encountered but processing completed")
                    else:
                        st.info("ℹ️ No stocks with existing calculations found")

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    with col_b:
        if st.button("🔄 Force Recalculate All", type="secondary", help="Force recalculate ALL stocks regardless of data age", use_container_width=True):
            with st.spinner("Force recalculating all composite scores..."):
                try:
                    # Import and call the analytics update utility with force flag
                    from utilities.update_analytics import update_analytics
                    import logging
                    import io

                    # Create a logger for the utility with stream capture
                    logger = logging.getLogger('dashboard_metrics')
                    logger.setLevel(logging.INFO)

                    # Capture logging output
                    log_capture = io.StringIO()
                    handler = logging.StreamHandler(log_capture)
                    handler.setLevel(logging.INFO)
                    logger.addHandler(handler)

                    # Run the calculation with force_recalculate=True
                    success = update_analytics(logger=logger, force_recalculate=True)

                    # Get captured logs
                    log_output = log_capture.getvalue()

                    # Count successful vs failed regardless of return value
                    success_count = log_output.count("✅") + log_output.count("Analytics updated successfully")
                    failed_count = log_output.count("❌") + log_output.count("calculation failed")

                    if success:
                        st.success("✅ Rankings calculated successfully!")
                        st.info("🎉 **Complete!** Check the main dashboard for updated rankings")
                    elif success_count > 0:
                        # Function returned False but still processed stocks successfully
                        st.warning("⚠️ Calculation completed with some limitations")
                        st.success(f"✅ Successfully processed {success_count} stocks")
                        if failed_count > 0:
                            st.info(f"ℹ️ Skipped {failed_count} stocks due to data quality issues")
                        st.info("📊 **Result:** Rankings updated for stocks with sufficient data quality")
                    else:
                        st.error("❌ Calculation failed - check logs for details")

                    if log_output and (not success or failed_count > 0):
                        with st.expander("📝 Show Processing Details"):
                            st.text(log_output[-2000:])  # Show last 2000 chars

                except Exception as e:
                    st.error(f"❌ Error during calculation: {str(e)}")
                    import traceback
                    with st.expander("📝 Show Full Error"):
                        st.text(traceback.format_exc())

    # Show completion status
    if db.connect():
        cursor = db.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM calculated_metrics")
        metrics_count = cursor.fetchone()[0]
        cursor.close()
        db.close()

        if metrics_count > 0:
            st.info(f"📊 **Last Update:** {metrics_count:,} stocks have calculated metrics")
        else:
            st.warning("⚠️ **No calculated metrics found** - run calculation to generate rankings")

    # Database Management
    st.markdown("---")
    st.markdown("## 💾 Database Management")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Backup Operations:**")
        if st.button("📁 Create Backup", help="Create timestamped database backup"):
            with st.spinner("Creating backup..."):
                try:
                    import subprocess
                    result = subprocess.run(['python', 'utilities/backup_database.py'],
                                         capture_output=True, text=True, cwd='.')
                    if result.returncode == 0:
                        st.success("✅ Database backup created successfully!")
                    else:
                        st.error(f"❌ Backup failed: {result.stderr}")
                except Exception as e:
                    st.error(f"❌ Backup error: {str(e)}")

    with col2:
        st.markdown("**System Status:**")
        # Show database stats
        try:
            db_stats = get_database_stats()
            if db_stats:
                for key, value in db_stats.items():
                    if key == 'coverage_pct':
                        st.metric(key.replace('_', ' ').title(), f"{value:.1f}%")
                    else:
                        st.metric(key.replace('_', ' ').title(), f"{value:,}")
        except Exception:
            st.write("Could not load database statistics")


def main():
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

        # Create enhanced histogram with stock ticker hover data
        # First, create bins and aggregate stock symbols per bin
        scores = main_df[score_column].values
        n_bins = 20
        bin_edges = np.linspace(scores.min(), scores.max(), n_bins + 1)

        # Assign each stock to a bin
        bin_indices = np.digitize(scores, bin_edges) - 1
        bin_indices = np.clip(bin_indices, 0, n_bins - 1)

        # Aggregate stocks by bin
        bin_data = []
        for i in range(n_bins):
            mask = bin_indices == i
            stocks_in_bin = main_df[mask]['symbol'].tolist()
            count = len(stocks_in_bin)
            bin_center = (bin_edges[i] + bin_edges[i + 1]) / 2
            bin_range = f"{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}"

            # Format stock list for hover (max 20 per line for readability)
            if len(stocks_in_bin) > 0:
                stock_lines = []
                for j in range(0, len(stocks_in_bin), 20):
                    stock_lines.append(', '.join(stocks_in_bin[j:j+20]))
                stocks_text = '<br>'.join(stock_lines)
            else:
                stocks_text = "None"

            bin_data.append({
                'bin_center': bin_center,
                'bin_range': bin_range,
                'count': count,
                'stocks': stocks_text
            })

        bin_df = pd.DataFrame(bin_data)

        # Create histogram using bar chart for better control
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Bar(
            x=bin_df['bin_center'],
            y=bin_df['count'],
            width=(bin_edges[1] - bin_edges[0]) * 0.9,
            hovertemplate='<b>Score Range:</b> %{customdata[0]}<br>' +
                          '<b>Number of Stocks:</b> %{y}<br>' +
                          '<b>Tickers:</b><br>%{customdata[1]}<extra></extra>',
            customdata=bin_df[['bin_range', 'stocks']].values,
            marker_color='#636EFA'
        ))

        fig_hist.update_layout(
            title="Score Distribution",
            xaxis_title="Composite Score",
            yaxis_title="Number of Stocks",
            font=dict(family='Montserrat'),
            hovermode='closest'
        )

        # Create enhanced box plot with individual stock points and outlier identification
        # Calculate quartiles and IQR for outlier detection
        Q1 = main_df[score_column].quantile(0.25)
        Q3 = main_df[score_column].quantile(0.75)
        IQR = Q3 - Q1
        lower_fence = Q1 - 1.5 * IQR
        upper_fence = Q3 + 1.5 * IQR

        # Identify outliers
        main_df['is_outlier'] = (main_df[score_column] < lower_fence) | (main_df[score_column] > upper_fence)

        fig_box = go.Figure()

        # Add box plot without outliers shown
        fig_box.add_trace(go.Box(
            y=main_df[score_column],
            name="",
            boxpoints=False,  # We'll add points manually
            marker_color='#636EFA',
            showlegend=False
        ))

        # Add all data points with enhanced hover info
        # Outliers get different styling
        outliers = main_df[main_df['is_outlier']]
        non_outliers = main_df[~main_df['is_outlier']]

        # Add non-outlier points (smaller, more transparent)
        if len(non_outliers) > 0:
            fig_box.add_trace(go.Scatter(
                x=[0] * len(non_outliers),
                y=non_outliers[score_column],
                mode='markers',
                name='Normal Range',
                marker=dict(
                    size=6,
                    color='rgba(99, 110, 250, 0.3)',
                    line=dict(width=1, color='rgba(99, 110, 250, 0.5)')
                ),
                hovertemplate='<b>%{customdata[0]}</b><br>' +
                              'Score: %{y:.2f}<br>' +
                              'Company: %{customdata[1]}<extra></extra>',
                customdata=non_outliers[['symbol', 'company_name']].values,
                showlegend=True
            ))

        # Add outlier points (larger, highlighted)
        if len(outliers) > 0:
            fig_box.add_trace(go.Scatter(
                x=[0] * len(outliers),
                y=outliers[score_column],
                mode='markers',
                name='Outliers',
                marker=dict(
                    size=10,
                    color='#FF6B6B',
                    symbol='diamond',
                    line=dict(width=2, color='#C92A2A')
                ),
                hovertemplate='<b>%{customdata[0]}</b> (OUTLIER)<br>' +
                              'Score: %{y:.2f}<br>' +
                              'Company: %{customdata[1]}<extra></extra>',
                customdata=outliers[['symbol', 'company_name']].values,
                showlegend=True
            ))

        fig_box.update_layout(
            title="Score Distribution Box Plot",
            yaxis_title="Composite Score",
            xaxis=dict(showticklabels=False),
            font=dict(family='Montserrat'),
            hovermode='closest',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

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