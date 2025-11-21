"""
API Configuration UI Components
Streamlit components for first-launch wizard and API key management
"""

import streamlit as st
import logging
from typing import Optional
from src.utils.api_key_manager import APIKeyManager, APIKeyStatus

logger = logging.getLogger(__name__)


def initialize_api_key_manager() -> APIKeyManager:
    """
    Initialize API Key Manager in Streamlit session state
    Returns the APIKeyManager instance
    """
    if 'api_key_manager' not in st.session_state:
        st.session_state.api_key_manager = APIKeyManager()
    return st.session_state.api_key_manager


def check_first_launch() -> bool:
    """
    Check if this is the first launch (no API keys configured)
    Returns True if first launch wizard should be shown
    """
    manager = initialize_api_key_manager()
    summary = manager.get_summary()

    # First launch if neither Reddit nor Claude is configured
    return not (summary['reddit_configured'] or summary['claude_configured'])


def render_first_launch_wizard():
    """
    Render the first-launch wizard for API configuration
    """
    st.markdown("# 🔑 Welcome to StockAnalyzer Pro!")

    st.markdown("""
    <div style='background-color: #f0f9ff; padding: 1.5rem; border-radius: 0.5rem; border-left: 4px solid #60B5E5; margin-bottom: 2rem;'>
        <h3 style='color: #1e40af; margin-top: 0;'>First Time Setup</h3>
        <p style='color: #1e3a8a; margin-bottom: 0;'>
            To get started with StockAnalyzer Pro, you'll need to provide your own API credentials.
            This ensures you have full control over your data collection and API usage costs.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### What You'll Need:")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **📱 Reddit API (Required for Social Sentiment)**
        - **Cost:** FREE
        - **Time:** ~5 minutes to set up
        - **Rate Limit:** 60 requests/minute
        - Used for: Collecting social media sentiment from Reddit
        """)

    with col2:
        st.markdown("""
        **🤖 Claude API (Required for Advanced Sentiment)**
        - **Cost:** Usage-based (50% discount via Batch API)
        - **Time:** ~5 minutes to set up
        - **You control costs:** Only pay for what you process
        - Used for: Advanced AI-powered sentiment analysis
        """)

    st.markdown("---")

    # Wizard steps
    tab1, tab2, tab3 = st.tabs(["1️⃣ Reddit API", "2️⃣ Claude API", "3️⃣ Complete Setup"])

    with tab1:
        render_reddit_setup_tab()

    with tab2:
        render_claude_setup_tab()

    with tab3:
        render_completion_tab()


def render_reddit_setup_tab():
    """Render Reddit API setup tab"""
    manager = initialize_api_key_manager()

    st.markdown("### Reddit API Setup")

    st.markdown("""
    <div style='background-color: #fff7ed; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #f59e0b; margin-bottom: 1rem;'>
        <strong>📋 Step-by-Step Instructions:</strong>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📖 How to get Reddit API credentials", expanded=True):
        st.markdown("""
        1. **Visit Reddit Apps:** [https://www.reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
        2. **Log in** to your Reddit account (or create one)
        3. **Scroll to bottom**, click **"create another app..."**
        4. **Fill in the form:**
           - **name:** `StockAnalyzer`
           - **type:** Select **"script"**
           - **description:** `Stock sentiment analysis tool`
           - **about url:** (leave blank)
           - **redirect uri:** `http://localhost:8080`
        5. **Click "create app"**
        6. **Copy your credentials:**
           - **Client ID:** (14 characters shown under the app name)
           - **Client Secret:** (27 characters, click "show" to reveal)
        """)

        st.info("💡 **Tip:** You can use any Reddit account. No special permissions needed!")

    # Input form
    st.markdown("### Enter Your Reddit Credentials")

    with st.form("reddit_api_form"):
        client_id = st.text_input(
            "Client ID",
            placeholder="14 characters (e.g., yeKIESP30pvI8o)",
            help="Find this under your app name in Reddit's app settings"
        )

        client_secret = st.text_input(
            "Client Secret",
            type="password",
            placeholder="27 characters",
            help="Click 'show' in Reddit's app settings to reveal"
        )

        user_agent = st.text_input(
            "User Agent",
            value="StockAnalyzer:v1.0",
            help="Identifies your app to Reddit (you can use the default)"
        )

        col1, col2 = st.columns([1, 1])

        with col1:
            save_reddit = st.form_submit_button("💾 Save Reddit Credentials", use_container_width=True)

        with col2:
            test_reddit = st.form_submit_button("🔍 Test Connection", use_container_width=True)

    # Handle form submissions
    if save_reddit:
        if client_id and client_secret and user_agent:
            if manager.save_reddit_credentials(client_id, client_secret, user_agent):
                st.success("✅ Reddit credentials saved successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to save credentials. Check the logs for details.")
        else:
            st.warning("⚠️ Please fill in all fields")

    if test_reddit:
        if not manager.has_reddit_credentials():
            st.warning("⚠️ Please save your credentials first")
        else:
            with st.spinner("Testing Reddit connection..."):
                status = manager.test_reddit_connection()
                if status.is_valid:
                    st.success("✅ Reddit API connection successful!")
                else:
                    st.error(f"❌ Connection failed: {status.error_message}")

    # Show current status
    if manager.has_reddit_credentials():
        st.markdown("""
        <div style='background-color: #f0fdf4; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #22c55e; margin-top: 1rem;'>
            ✅ <strong>Reddit API configured!</strong> You can now collect social sentiment data.
        </div>
        """, unsafe_allow_html=True)


def render_claude_setup_tab():
    """Render Claude API setup tab"""
    manager = initialize_api_key_manager()

    st.markdown("### Claude API Setup")

    st.markdown("""
    <div style='background-color: #fff7ed; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #f59e0b; margin-bottom: 1rem;'>
        <strong>📋 Step-by-Step Instructions:</strong>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📖 How to get Claude API key", expanded=True):
        st.markdown("""
        1. **Visit Anthropic Console:** [https://console.anthropic.com/](https://console.anthropic.com/)
        2. **Sign up** for an account (or log in)
        3. **Navigate** to "API Keys" section
        4. **Click "Create Key"**
        5. **Name it:** `StockAnalyzer`
        6. **Copy the key** (starts with `sk-ant-api03-`)
        7. **Save it securely** - you won't be able to see it again!
        """)

        st.warning("⚠️ **Important:** Add credits to your Anthropic account before running sentiment analysis.")

    # Cost estimate
    st.markdown("### 💰 Cost Information")
    st.markdown("""
    **How Pricing Works:**
    - Usage-based pricing (pay only for what you process)
    - **50% discount** via Anthropic's Batch API
    - You choose which articles to analyze
    - Processing happens in batches you submit manually

    **Typical Usage:**
    - **Small portfolios** (10-20 stocks): $1-5 initial, cents for updates
    - **Full S&P 500**: Variable depending on date range and articles collected
    - **Monthly updates**: Process only new articles (typically minimal cost)

    💡 **You have full control:** Choose when and what to process.
    """)

    # Input form
    st.markdown("### Enter Your Claude API Key")

    with st.form("claude_api_form"):
        api_key = st.text_input(
            "Claude API Key",
            type="password",
            placeholder="sk-ant-api03-...",
            help="Your Anthropic API key (starts with sk-ant-api03-)"
        )

        col1, col2 = st.columns([1, 1])

        with col1:
            save_claude = st.form_submit_button("💾 Save Claude API Key", use_container_width=True)

        with col2:
            test_claude = st.form_submit_button("🔍 Test Connection", use_container_width=True)

    # Handle form submissions
    if save_claude:
        if api_key:
            if api_key.startswith("sk-ant-api03-"):
                if manager.save_api_key(APIKeyManager.CLAUDE_API_KEY, api_key):
                    st.success("✅ Claude API key saved successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to save API key. Check the logs for details.")
            else:
                st.error("❌ Invalid API key format. Claude keys start with 'sk-ant-api03-'")
        else:
            st.warning("⚠️ Please enter your API key")

    if test_claude:
        if not manager.has_claude_credentials():
            st.warning("⚠️ Please save your API key first")
        else:
            with st.spinner("Testing Claude API connection..."):
                status = manager.test_claude_connection()
                if status.is_valid:
                    st.success("✅ Claude API connection successful!")
                else:
                    st.error(f"❌ Connection failed: {status.error_message}")

    # Show current status
    if manager.has_claude_credentials():
        st.markdown("""
        <div style='background-color: #f0fdf4; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #22c55e; margin-top: 1rem;'>
            ✅ <strong>Claude API configured!</strong> You can now run advanced sentiment analysis.
        </div>
        """, unsafe_allow_html=True)


def render_completion_tab():
    """Render setup completion tab"""
    manager = initialize_api_key_manager()
    summary = manager.get_summary()

    st.markdown("### 🎉 Setup Status")

    # Status cards
    col1, col2 = st.columns(2)

    with col1:
        if summary['reddit_configured']:
            st.markdown("""
            <div style='background-color: #f0fdf4; padding: 1rem; border-radius: 0.5rem; border: 2px solid #22c55e;'>
                <h4 style='color: #16a34a; margin-top: 0;'>✅ Reddit API</h4>
                <p style='margin-bottom: 0;'>Configured and ready!</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style='background-color: #fef2f2; padding: 1rem; border-radius: 0.5rem; border: 2px solid #ef4444;'>
                <h4 style='color: #dc2626; margin-top: 0;'>❌ Reddit API</h4>
                <p style='margin-bottom: 0;'>Not configured yet</p>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        if summary['claude_configured']:
            st.markdown("""
            <div style='background-color: #f0fdf4; padding: 1rem; border-radius: 0.5rem; border: 2px solid #22c55e;'>
                <h4 style='color: #16a34a; margin-top: 0;'>✅ Claude API</h4>
                <p style='margin-bottom: 0;'>Configured and ready!</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style='background-color: #fef2f2; padding: 1rem; border-radius: 0.5rem; border: 2px solid #ef4444;'>
                <h4 style='color: #dc2626; margin-top: 0;'>❌ Claude API</h4>
                <p style='margin-bottom: 0;'>Not configured yet</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # Next steps
    if summary['full_functionality']:
        st.success("🎉 **All set!** You're ready to use StockAnalyzer Pro with full functionality.")

        if st.button("🚀 Continue to Dashboard", type="primary", use_container_width=True):
            st.session_state.setup_complete = True
            st.rerun()

    elif summary['reddit_configured'] or summary['claude_configured']:
        st.warning("""
        ⚠️ **Partial Configuration**

        You've configured some APIs, but not all features will be available:
        - **Reddit API:** Required for social sentiment collection
        - **Claude API:** Required for advanced sentiment analysis

        You can continue with limited functionality or complete the setup.
        """)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Continue with Limited Features", use_container_width=True):
                st.session_state.setup_complete = True
                st.rerun()
        with col2:
            if st.button("Complete Setup", type="primary", use_container_width=True):
                st.info("Please configure the remaining APIs in the tabs above.")

    else:
        st.info("""
        📝 **Next Steps:**

        1. Go to the **Reddit API** tab and enter your credentials
        2. Go to the **Claude API** tab and enter your API key
        3. Return here to complete the setup

        Or you can skip this for now and configure APIs later in Settings.
        """)

        if st.button("⏭️ Skip for Now (Limited Functionality)", use_container_width=True):
            st.session_state.setup_complete = True
            st.rerun()


def render_api_settings_page():
    """
    Render the API Configuration settings page
    """
    manager = initialize_api_key_manager()
    summary = manager.get_summary()

    st.title("⚙️ API Configuration")

    st.markdown("""
    Manage your API credentials securely. All keys are stored in your system's keychain
    and never bundled with the application.
    """)

    # Current status overview
    st.markdown("### 📊 Current Status")

    col1, col2, col3 = st.columns(3)

    with col1:
        status_color = "#22c55e" if summary['reddit_configured'] else "#ef4444"
        st.markdown(f"""
        <div style='text-align: center; padding: 1rem; border-radius: 0.5rem; background-color: {status_color}20; border: 2px solid {status_color};'>
            <h3 style='margin: 0; color: {status_color};'>Reddit API</h3>
            <p style='margin: 0.5rem 0 0 0;'>{'✅ Configured' if summary['reddit_configured'] else '❌ Not Configured'}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        status_color = "#22c55e" if summary['claude_configured'] else "#ef4444"
        st.markdown(f"""
        <div style='text-align: center; padding: 1rem; border-radius: 0.5rem; background-color: {status_color}20; border: 2px solid {status_color};'>
            <h3 style='margin: 0; color: {status_color};'>Claude API</h3>
            <p style='margin: 0.5rem 0 0 0;'>{'✅ Configured' if summary['claude_configured'] else '❌ Not Configured'}</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        functionality_text = "Full" if summary['full_functionality'] else "Limited"
        functionality_color = "#22c55e" if summary['full_functionality'] else "#f59e0b"
        st.markdown(f"""
        <div style='text-align: center; padding: 1rem; border-radius: 0.5rem; background-color: {functionality_color}20; border: 2px solid {functionality_color};'>
            <h3 style='margin: 0; color: {functionality_color};'>Functionality</h3>
            <p style='margin: 0.5rem 0 0 0;'>{functionality_text}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # API Configuration tabs
    tab1, tab2 = st.tabs(["Reddit API", "Claude API"])

    with tab1:
        render_reddit_config_section(manager)

    with tab2:
        render_claude_config_section(manager)


def render_reddit_config_section(manager: APIKeyManager):
    """Render Reddit API configuration section"""
    st.markdown("### Reddit API Configuration")

    if manager.has_reddit_credentials():
        st.success("✅ Reddit API credentials are configured")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Update Credentials", use_container_width=True):
                st.session_state.show_reddit_form = True
        with col2:
            if st.button("🗑️ Delete Credentials", use_container_width=True, type="secondary"):
                if manager.delete_reddit_credentials():
                    st.success("Credentials deleted successfully")
                    st.rerun()
                else:
                    st.error("Failed to delete credentials")

    if not manager.has_reddit_credentials() or st.session_state.get('show_reddit_form', False):
        render_reddit_setup_tab()
        if manager.has_reddit_credentials():
            st.session_state.show_reddit_form = False


def render_claude_config_section(manager: APIKeyManager):
    """Render Claude API configuration section"""
    st.markdown("### Claude API Configuration")

    if manager.has_claude_credentials():
        st.success("✅ Claude API key is configured")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Update API Key", use_container_width=True):
                st.session_state.show_claude_form = True
        with col2:
            if st.button("🗑️ Delete API Key", use_container_width=True, type="secondary"):
                if manager.delete_api_key(APIKeyManager.CLAUDE_API_KEY):
                    st.success("API key deleted successfully")
                    st.rerun()
                else:
                    st.error("Failed to delete API key")

    if not manager.has_claude_credentials() or st.session_state.get('show_claude_form', False):
        render_claude_setup_tab()
        if manager.has_claude_credentials():
            st.session_state.show_claude_form = False


def render_api_status_sidebar():
    """
    Render API status indicators in the sidebar
    """
    manager = initialize_api_key_manager()
    summary = manager.get_summary()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔑 API Status")

    # Reddit status
    reddit_icon = "✅" if summary['reddit_configured'] else "❌"
    reddit_color = "#22c55e" if summary['reddit_configured'] else "#ef4444"
    st.sidebar.markdown(f"""
    <div style='padding: 0.5rem; border-radius: 0.25rem; background-color: {reddit_color}20; margin-bottom: 0.5rem;'>
        {reddit_icon} <strong>Reddit:</strong> {'Configured' if summary['reddit_configured'] else 'Not configured'}
    </div>
    """, unsafe_allow_html=True)

    # Claude status
    claude_icon = "✅" if summary['claude_configured'] else "❌"
    claude_color = "#22c55e" if summary['claude_configured'] else "#ef4444"
    st.sidebar.markdown(f"""
    <div style='padding: 0.5rem; border-radius: 0.25rem; background-color: {claude_color}20; margin-bottom: 0.5rem;'>
        {claude_icon} <strong>Claude:</strong> {'Configured' if summary['claude_configured'] else 'Not configured'}
    </div>
    """, unsafe_allow_html=True)

    # Link to settings
    if st.sidebar.button("⚙️ Manage API Keys", use_container_width=True):
        st.session_state.current_page = "API Settings"
        st.rerun()

    return summary
