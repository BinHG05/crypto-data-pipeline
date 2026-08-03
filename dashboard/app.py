import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Page setup for premium production aesthetic
st.set_page_config(
    page_title="Crypto Market Insights & Intelligence Portal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern dark glassmorphism UI theme
st.markdown(
    """
<style>
    /* Main container background */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Headers styling */
    h1, h2, h3 {
        color: #ffffff !important;
        font-weight: 700;
        letter-spacing: -0.5px;
    }

    /* Professional Top metric cards */
    .metric-card {
        background: linear-gradient(135deg, rgba(22, 27, 34, 0.9) 0%, rgba(13, 17, 23, 0.9) 100%);
        border: 1px solid rgba(48, 54, 61, 0.8);
        border-radius: 14px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        border-color: #58a6ff;
        transform: translateY(-2px);
    }
    .metric-title {
        font-size: 13px;
        text-transform: uppercase;
        color: #8b949e;
        margin-bottom: 6px;
        font-weight: 600;
        letter-spacing: 0.8px;
    }
    .metric-value {
        font-size: 32px;
        font-weight: 800;
        color: #ffffff;
    }
    .metric-sub {
        font-size: 13px;
        font-weight: 600;
        margin-top: 6px;
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
    }

    /* Status badge colors */
    .badge-green { background: rgba(57, 211, 83, 0.15); color: #39d353; border: 1px solid rgba(57, 211, 83, 0.3); }
    .badge-yellow { background: rgba(249, 226, 175, 0.15); color: #f9e2af; border: 1px solid rgba(249, 226, 175, 0.3); }
    .badge-red { background: rgba(248, 81, 73, 0.15); color: #f85149; border: 1px solid rgba(248, 81, 73, 0.3); }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #161b22 !important;
        border-right: 1px solid #30363d !important;
    }
</style>
""",
    unsafe_allow_html=True,
)


def load_env():
    """Manually reads and loads environment variables from project .env file."""
    base_dir = Path(__file__).resolve().parent.parent
    env_path = base_dir / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    val = val.strip("'\"")
                    os.environ[key] = val


# Load credentials
load_env()

# Retrieve AWS configs
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "ap-southeast-1")
AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME", "")
ATHENA_S3_STAGING = f"s3://{AWS_S3_BUCKET_NAME}/athena_results/"


@st.cache_resource
def get_athena_connection():
    """Creates a thread-safe connection to AWS Athena."""
    from pyathena import connect

    try:
        return connect(
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION,
            s3_staging_dir=ATHENA_S3_STAGING,
            schema_name="crypto_athena",
        )
    except Exception as e:
        st.error(f"Athena Connection Error: {e}")
        return None


def run_query(query: str) -> pd.DataFrame:
    """Runs a SQL query against Athena database and returns a Pandas DataFrame."""
    conn = get_athena_connection()
    if conn is None:
        return pd.DataFrame()
    try:
        return pd.read_sql(query, conn)
    except Exception as e:
        st.error(f"Query execution error: {e}")
        return pd.DataFrame()


# Coin symbols mapping dictionary
COIN_NAME_MAP = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "solana": "SOL",
    "cardano": "ADA",
    "ripple": "XRP",
    "polkadot": "DOT",
    "avalanche-2": "AVAX",
    "dogecoin": "DOGE",
}

ALL_COINS = ["BTC", "ETH", "SOL", "ADA", "XRP", "DOT", "AVAX", "DOGE"]

# ==========================================
# INITIALIZE STATE
# ==========================================
if "fg_history_df" not in st.session_state:
    st.session_state.fg_history_df = pd.DataFrame()
if "prices_df" not in st.session_state:
    st.session_state.prices_df = pd.DataFrame()
if "reddit_mentions_df" not in st.session_state:
    st.session_state.reddit_mentions_df = pd.DataFrame()
if "initial_fetch_done" not in st.session_state:
    st.session_state.initial_fetch_done = False


def fetch_all_dashboard_data():
    """Fetches all market datasets from AWS Athena Data Lake."""
    st.session_state.fg_history_df = run_query(
        """
        SELECT CAST(value AS INT) as value, value_classification, dt
        FROM crypto_athena.fear_greed_index
        ORDER BY dt DESC
        LIMIT 90
    """
    )

    st.session_state.prices_df = run_query(
        """
        SELECT 
            CASE LOWER(symbol)
                WHEN 'bitcoin' THEN 'BTC'
                WHEN 'ethereum' THEN 'ETH'
                WHEN 'solana' THEN 'SOL'
                WHEN 'cardano' THEN 'ADA'
                WHEN 'ripple' THEN 'XRP'
                WHEN 'polkadot' THEN 'DOT'
                WHEN 'avalanche-2' THEN 'AVAX'
                WHEN 'dogecoin' THEN 'DOGE'
                ELSE UPPER(symbol)
            END AS symbol,
            price, timestamp, dt
        FROM crypto_athena.coingecko_prices
        ORDER BY dt DESC, timestamp DESC
    """
    )

    st.session_state.reddit_mentions_df = run_query(
        """
        SELECT
            dt AS report_date,
            COUNT(CASE WHEN LOWER(title) LIKE '%btc%' OR LOWER(title) LIKE '%bitcoin%' THEN 1 END) AS btc_mentions,
            COUNT(CASE WHEN LOWER(title) LIKE '%eth%' OR LOWER(title) LIKE '%ethereum%' THEN 1 END) AS eth_mentions,
            COUNT(CASE WHEN LOWER(title) LIKE '%sol%' OR LOWER(title) LIKE '%solana%' THEN 1 END) AS sol_mentions,
            COUNT(CASE WHEN LOWER(title) LIKE '%ada%' OR LOWER(title) LIKE '%cardano%' THEN 1 END) AS ada_mentions,
            COUNT(CASE WHEN LOWER(title) LIKE '%xrp%' OR LOWER(title) LIKE '%ripple%' THEN 1 END) AS xrp_mentions,
            COUNT(CASE WHEN LOWER(title) LIKE '%dot%' OR LOWER(title) LIKE '%polkadot%' THEN 1 END) AS dot_mentions,
            COUNT(CASE WHEN LOWER(title) LIKE '%avax%' OR LOWER(title) LIKE '%avalanche%' THEN 1 END) AS avax_mentions,
            COUNT(CASE WHEN LOWER(title) LIKE '%doge%' OR LOWER(title) LIKE '%dogecoin%' THEN 1 END) AS doge_mentions
        FROM crypto_athena.reddit_posts
        GROUP BY dt
        ORDER BY dt ASC
    """
    )
    st.session_state.initial_fetch_done = True


# Auto-fetch data on first load if credentials present
if not st.session_state.initial_fetch_done and AWS_ACCESS_KEY_ID:
    fetch_all_dashboard_data()

# ==========================================
# SIDEBAR - Controls & Filters
# ==========================================
with st.sidebar:
    st.image("https://cryptologos.cc/logos/bitcoin-btc-logo.png", width=50)
    st.title("Market Filters")
    st.markdown("---")

    days_to_show = st.selectbox(
        "Timeline Range",
        options=[7, 15, 30, 60, 90],
        index=2,
        format_func=lambda x: f"Last {x} Days",
    )

    selected_coins = st.multiselect(
        "Watchlist Tokens",
        options=ALL_COINS,
        default=["BTC", "ETH", "SOL", "ADA", "XRP"],
    )

    st.markdown("---")
    if st.button("🔄 Sync Latest Market Data", use_container_width=True):
        with st.spinner("Syncing latest Data Lake partitions..."):
            fetch_all_dashboard_data()
            st.rerun()

# ==========================================
# HEADER SECTION
# ==========================================
st.markdown("# ⚡ Crypto Market Intelligence & Sentiment Portal")
st.markdown(
    "Real-time market analytics, sentiment indicators, and social volume correlation powered by **Data Lake & AWS Athena Serverless Engine**."
)
st.markdown("---")

# Read dataframes from Session State
fg_history_df = st.session_state.fg_history_df
prices_df = st.session_state.prices_df
reddit_mentions_df = st.session_state.reddit_mentions_df

# ==========================================
# SUMMARY METRIC CARDS (CLEAN & PROFESSIONAL)
# ==========================================
kpi_cols = st.columns(4)

# 1. Market Sentiment Score (Fear & Greed)
with kpi_cols[0]:
    if not fg_history_df.empty:
        fg_val = int(fg_history_df["value"].iloc[0])
        fg_class = fg_history_df["value_classification"].iloc[0]

        badge_style = "badge-yellow"
        if fg_val < 35:
            badge_style = "badge-red"
        elif fg_val > 65:
            badge_style = "badge-green"

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Fear & Greed Index</div>
                <div class="metric-value">{fg_val} <span style="font-size:16px; color:#8b949e;">/ 100</span></div>
                <div class="metric-sub {badge_style}">{fg_class}</div>
            </div>
        """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-title">Fear & Greed Index</div>
                <div class="metric-value">N/A</div>
                <div class="metric-sub badge-yellow">No Data</div>
            </div>
        """,
            unsafe_allow_html=True,
        )

# Function to render clean token price card
def render_token_card(container, token_symbol, token_name):
    price_str = "N/A"
    badge_text = "Active"
    badge_style = "badge-green"

    if not prices_df.empty:
        token_row = prices_df[prices_df["symbol"].str.upper() == token_symbol]
        if not token_row.empty:
            val = token_row["price"].iloc[0]
            if val < 1.0:
                price_str = f"${val:,.4f}"
            else:
                price_str = f"${val:,.2f}"

    with container:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">{token_name} ({token_symbol})</div>
                <div class="metric-value">{price_str}</div>
                <div class="metric-sub {badge_style}">{badge_text}</div>
            </div>
        """,
            unsafe_allow_html=True,
        )


render_token_card(kpi_cols[1], "BTC", "Bitcoin")
render_token_card(kpi_cols[2], "ETH", "Ethereum")
render_token_card(kpi_cols[3], "SOL", "Solana")

st.markdown("###")

# ==========================================
# CHARTS ROW 1
# ==========================================
col1, col2 = st.columns(2)

# Chart 1: Fear & Greed Trend
with col1:
    st.subheader(f"📈 Fear & Greed Sentiment Trend (Last {days_to_show} Days)")
    if not fg_history_df.empty:
        fg_plot = fg_history_df.head(days_to_show).iloc[::-1].reset_index(drop=True)
        fig_fg = go.Figure()

        fig_fg.add_trace(
            go.Scatter(
                x=fg_plot["dt"],
                y=fg_plot["value"],
                mode="lines+markers",
                name="Sentiment Index",
                line=dict(color="#ff9900", width=3),
                marker=dict(size=5, color="#ff9900"),
                fill="tozeroy",
                fillcolor="rgba(255, 153, 0, 0.08)",
            )
        )

        fg_plot["7_day_ma"] = fg_plot["value"].rolling(window=7).mean()
        if not fg_plot["7_day_ma"].isna().all():
            fig_fg.add_trace(
                go.Scatter(
                    x=fg_plot["dt"],
                    y=fg_plot["7_day_ma"],
                    mode="lines",
                    name="7-Day Moving Avg",
                    line=dict(color="#58a6ff", width=2, dash="dash"),
                )
            )

        fig_fg.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=True, gridcolor="#21262d", title="Date", color="#c9d1d9"),
            yaxis=dict(showgrid=True, gridcolor="#21262d", title="Index Value (0-100)", range=[0, 100], color="#c9d1d9"),
            legend=dict(font=dict(color="#c9d1d9")),
            margin=dict(l=20, r=20, t=20, b=20),
            height=380,
        )
        st.plotly_chart(fig_fg, use_container_width=True)
    else:
        st.info("No historical Fear & Greed data available.")

# Chart 2: Social Mentions by Token
with col2:
    st.subheader(f"🔥 Reddit Social Discussion Volume (Last {days_to_show} Days)")
    if not reddit_mentions_df.empty:
        recent_reddit = reddit_mentions_df.tail(days_to_show)
        mentions_list = []

        col_map = {
            "BTC": "btc_mentions",
            "ETH": "eth_mentions",
            "SOL": "sol_mentions",
            "ADA": "ada_mentions",
            "XRP": "xrp_mentions",
            "DOT": "dot_mentions",
            "AVAX": "avax_mentions",
            "DOGE": "doge_mentions",
        }

        for coin in selected_coins:
            c_col = col_map.get(coin)
            if c_col in recent_reddit.columns:
                total_m = int(recent_reddit[c_col].sum())
                mentions_list.append({"Token": coin, "Mentions": total_m})

        summed_mentions = pd.DataFrame(mentions_list)

        if not summed_mentions.empty and summed_mentions["Mentions"].sum() > 0:
            fig_bar = px.bar(
                summed_mentions,
                x="Token",
                y="Mentions",
                color="Token",
                color_discrete_sequence=["#ff9900", "#8c8cff", "#39d353", "#0033ad", "#23292f", "#e6007a", "#e84142", "#c2a633"],
                labels={"Token": "Cryptocurrency", "Mentions": "Total Reddit Mentions"},
            )
            fig_bar.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False, color="#c9d1d9"),
                yaxis=dict(showgrid=True, gridcolor="#21262d", color="#c9d1d9"),
                showlegend=False,
                margin=dict(l=20, r=20, t=20, b=20),
                height=380,
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No social mentions recorded for the selected tokens in this timeframe.")
    else:
        st.info("No Reddit post data found in Athena.")

st.markdown("---")

# ==========================================
# CHARTS ROW 2 - DUAL AXIS CORRELATION
# ==========================================
st.subheader(f"📊 Price vs Social Volume Correlation (BTC) - Last {days_to_show} Days")
st.markdown("Overlaying Bitcoin price action against Reddit discussion spikes to identify market hype cycles.")

if not prices_df.empty and not reddit_mentions_df.empty:
    btc_prices = prices_df[prices_df["symbol"] == "BTC"].copy()
    if not btc_prices.empty:
        btc_prices_grouped = btc_prices.groupby("dt")["price"].mean().reset_index()
        btc_prices_grouped.columns = ["report_date", "avg_price"]

        btc_mentions = reddit_mentions_df[["report_date", "btc_mentions"]].copy()
        btc_mentions.columns = ["report_date", "mention_count"]

        corr_df = pd.merge(btc_prices_grouped, btc_mentions, on="report_date", how="left")
        corr_df["mention_count"] = corr_df["mention_count"].fillna(0)
        corr_df = corr_df.sort_values("report_date").reset_index(drop=True)
        corr_df = corr_df.tail(days_to_show)

        if not corr_df.empty:
            fig_corr = go.Figure()

            fig_corr.add_trace(
                go.Scatter(
                    x=corr_df["report_date"],
                    y=corr_df["avg_price"],
                    mode="lines+markers",
                    name="BTC Price ($)",
                    line=dict(color="#39d353", width=3),
                    yaxis="y1",
                )
            )

            fig_corr.add_trace(
                go.Bar(
                    x=corr_df["report_date"],
                    y=corr_df["mention_count"],
                    name="Reddit Discussion Count",
                    marker=dict(color="rgba(88, 166, 255, 0.35)"),
                    yaxis="y2",
                )
            )

            fig_corr.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=True, gridcolor="#21262d", title="Date", color="#c9d1d9"),
                yaxis1=dict(
                    title=dict(text="Bitcoin Price ($)", font=dict(color="#39d353")),
                    tickfont=dict(color="#39d353"),
                    showgrid=True,
                    gridcolor="#21262d",
                    color="#39d353",
                ),
                yaxis2=dict(
                    title=dict(text="Reddit Discussion Spikes", font=dict(color="#58a6ff")),
                    tickfont=dict(color="#58a6ff"),
                    overlaying="y",
                    side="right",
                    showgrid=False,
                    color="#58a6ff",
                ),
                legend=dict(x=0.01, y=0.99, font=dict(color="#c9d1d9")),
                margin=dict(l=20, r=20, t=20, b=20),
                height=450,
            )
            st.plotly_chart(fig_corr, use_container_width=True)
        else:
            st.info("No correlation data available for the selected timeline.")
    else:
        st.info("Bitcoin price data is missing.")
else:
    st.info("Pricing or Reddit data is unavailable.")
