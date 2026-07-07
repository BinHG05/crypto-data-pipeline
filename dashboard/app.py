import os
import sys
from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.graph_objects as go 
import plotly.express as px

# Page setup for premium aesthetic
st.set_page_config(
    page_title="Crypto Market Insights & Sentiment Hub",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark glassmorphism UI theme
st.markdown("""
<style>
    /* Main container background */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
        font-family: 'Outfit', sans-serif;
    }
    
    /* Headers styling */
    h1, h2, h3 {
        color: #ffffff !important;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    /* Top metric cards (Glassmorphic) */
    .metric-card {
        background: rgba(22, 27, 34, 0.7);
        border: 1px solid rgba(48, 54, 61, 0.8);
        border-radius: 12px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
    }
    .metric-title {
        font-size: 14px;
        text-transform: uppercase;
        color: #8b949e;
        margin-bottom: 8px;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    .metric-value {
        font-size: 36px;
        font-weight: 800;
        color: #58a6ff;
    }
    .metric-label {
        font-size: 16px;
        font-weight: 600;
        margin-top: 5px;
    }
    
    /* Panel for welcome prompt */
    .welcome-panel {
        background: rgba(22, 27, 34, 0.9);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 40px;
        text-align: center;
        max-width: 700px;
        margin: 50px auto;
        box-shadow: 0 8px 30px rgba(0,0,0,0.5);
    }
    
    /* Glowing accents */
    .glow-green { color: #39d353 !important; }
    .glow-yellow { color: #f9e2af !important; }
    .glow-red { color: #f85149 !important; }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #161b22 !important;
        border-right: 1px solid #30363d !important;
    }
</style>
""", unsafe_allow_html=True)


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
    # Defer import to prevent threading compile lockups during server startup
    from pyathena import connect
    try:
        return connect(
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION,
            s3_staging_dir=ATHENA_S3_STAGING,
            schema_name="crypto_athena"
        )
    except Exception as e:
        st.error(f"Failed to connect to AWS Athena: {e}")
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


# ==========================================
# INITIALIZE STATE
# ==========================================
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False
    st.session_state.fg_history_df = pd.DataFrame()
    st.session_state.prices_df = pd.DataFrame()
    st.session_state.reddit_mentions_df = pd.DataFrame()

# ==========================================
# SIDEBAR - Config & Status
# ==========================================
with st.sidebar:
    st.image("https://cryptologos.cc/logos/bitcoin-btc-logo.png", width=60)
    st.title("Settings")
    st.markdown("---")
    
    st.markdown("### Connection Status")
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY and AWS_S3_BUCKET_NAME:
        st.success("Credentials Loaded Successfully")
    else:
        st.warning("AWS Credentials Missing in .env")

    st.info(f"**Athena Database:** `crypto_athena`\n\n**Region:** `{AWS_REGION}`")
    
    st.markdown("---")
    st.markdown("### Controls")
    if st.session_state.data_loaded:
        days_to_show = st.selectbox(
            "Select Timeline",
            options=[7, 15, 30],
            index=2,
            format_func=lambda x: f"Last {x} Days"
        )
        selected_coins = st.multiselect(
            "Coins to Analyze",
            options=["BTC", "ETH", "SOL"],
            default=["BTC", "ETH", "SOL"]
        )
        st.markdown("---")
        if st.button("🔄 Refresh Data"):
            st.session_state.data_loaded = False
            st.rerun()
    else:
        st.info("Load data to enable controls")

# ==========================================
# HEADER SECTION
# ==========================================
st.markdown("# 📊 Crypto Market Insights & Sentiment Hub")
st.markdown("Analyzing real-time correlation between token price actions and Reddit social sentiments via **AWS S3, Athena, and Streamlit**.")
st.markdown("---")

# Verify connection
if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
    st.info("Please fill in your AWS credentials in your project's `.env` file to start querying.")
    st.stop()

# ==========================================
# CONNECT & LOAD SCREEN (NON-BLOCKING)
# ==========================================
if not st.session_state.data_loaded:
    st.markdown(f"""
        <div class="welcome-panel">
            <h2>🔌 Ready to Connect</h2>
            <p style="color: #8b949e; margin-top: 10px; font-size: 15px;">
                AWS credentials and S3 schemas are configured. Click the button below to trigger AWS Athena serverless queries on your S3 Parquet data warehouse.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    col_c1, col_c2, col_c3 = st.columns([1, 2, 1])
    with col_c2:
        if st.button("📊 Connect & Fetch Latest Market Insights", use_container_width=True):
            with st.spinner("Executing serverless queries on AWS Athena..."):
                # 1. Fetch historical Fear & Greed (covers current too)
                st.session_state.fg_history_df = run_query("""
                    SELECT CAST(value AS INT) as value, value_classification, dt 
                    FROM crypto_athena.fear_greed_index 
                    ORDER BY dt DESC 
                    LIMIT 30
                """)

                # 2. Fetch latest prices for summary metrics
                # Note: CoinGecko API stores full names (bitcoin, ethereum), map to short symbols
                st.session_state.prices_df = run_query("""
                    SELECT 
                        CASE LOWER(symbol)
                            WHEN 'bitcoin' THEN 'btc'
                            WHEN 'ethereum' THEN 'eth'
                            WHEN 'solana' THEN 'sol'
                            ELSE LOWER(symbol)
                        END AS symbol,
                        price, timestamp, dt
                    FROM crypto_athena.coingecko_prices
                    ORDER BY dt DESC, timestamp DESC
                """)

                # 3. Fetch Reddit mentions aggregated by day for BTC, ETH, SOL
                st.session_state.reddit_mentions_df = run_query("""
                    SELECT
                        dt AS report_date,
                        COUNT(CASE WHEN LOWER(title) LIKE '%btc%' OR LOWER(title) LIKE '%bitcoin%' THEN 1 END) AS btc_mentions,
                        COUNT(CASE WHEN LOWER(title) LIKE '%eth%' OR LOWER(title) LIKE '%ethereum%' THEN 1 END) AS eth_mentions,
                        COUNT(CASE WHEN LOWER(title) LIKE '%sol%' OR LOWER(title) LIKE '%solana%' THEN 1 END) AS sol_mentions
                    FROM crypto_athena.reddit_posts
                    GROUP BY dt
                    ORDER BY dt ASC
                """)
                
                st.session_state.data_loaded = True
                st.rerun()

else:
    # Read dataframes from Session State
    fg_history_df = st.session_state.fg_history_df
    prices_df = st.session_state.prices_df
    reddit_mentions_df = st.session_state.reddit_mentions_df

    # ==========================================
    # SUMMARY METRIC CARDS
    # ==========================================
    kpi_cols = st.columns(4)

    # 1. Market Sentiment Score (Fear & Greed)
    with kpi_cols[0]:
        if not fg_history_df.empty:
            fg_val = int(fg_history_df["value"].iloc[0])
            fg_class = fg_history_df["value_classification"].iloc[0]
            
            color_class = "glow-yellow"
            if fg_val < 30:
                color_class = "glow-red"
            elif fg_val > 70:
                color_class = "glow-green"
                
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Fear & Greed Score</div>
                    <div class="metric-value">{fg_val}</div>
                    <div class="metric-label {color_class}">{fg_class}</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="metric-card">
                    <div class="metric-title">Fear & Greed Score</div>
                    <div class="metric-value">N/A</div>
                    <div class="metric-label">No Data</div>
                </div>
            """, unsafe_allow_html=True)

    # 2. BTC Price
    with kpi_cols[1]:
        btc_price = "N/A"
        if not prices_df.empty:
            btc_row = prices_df[prices_df["symbol"] == "btc"]
            if not btc_row.empty:
                btc_price = f"${btc_row['price'].iloc[0]:,.2f}"
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Bitcoin (BTC) Price</div>
                <div class="metric-value">{btc_price}</div>
                <div class="metric-label glow-green">Coingecko API</div>
            </div>
        """, unsafe_allow_html=True)

    # 3. ETH Price
    with kpi_cols[2]:
        eth_price = "N/A"
        if not prices_df.empty:
            eth_row = prices_df[prices_df["symbol"] == "eth"]
            if not eth_row.empty:
                eth_price = f"${eth_row['price'].iloc[0]:,.2f}"
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Ethereum (ETH) Price</div>
                <div class="metric-value">{eth_price}</div>
                <div class="metric-label glow-green">Coingecko API</div>
            </div>
        """, unsafe_allow_html=True)

    # 4. SOL Price
    with kpi_cols[3]:
        sol_price = "N/A"
        if not prices_df.empty:
            sol_row = prices_df[prices_df["symbol"] == "sol"]
            if not sol_row.empty:
                sol_price = f"${sol_row['price'].iloc[0]:,.2f}"
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Solana (SOL) Price</div>
                <div class="metric-value">{sol_price}</div>
                <div class="metric-label glow-green">Coingecko API</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("###")

    # ==========================================
    # CHARTS ROW 1
    # ==========================================
    col1, col2 = st.columns(2)

    # Chart 1: Fear & Greed Trend (7 days vs 30 days)
    with col1:
        st.subheader(f"📈 Fear & Greed Index Trend (Last {days_to_show} Days)")
        if not fg_history_df.empty:
            # Filter by days_to_show
            fg_history_plot = fg_history_df.head(days_to_show).iloc[::-1].reset_index(drop=True)
            fig_fg = go.Figure()
            
            fig_fg.add_trace(go.Scatter(
                x=fg_history_plot["dt"],
                y=fg_history_plot["value"],
                mode="lines+markers",
                name="Fear & Greed Index",
                line=dict(color="#ff9900", width=3),
                marker=dict(size=6, color="#ff9900"),
                fill="tozeroy",
                fillcolor="rgba(255, 153, 0, 0.1)"
            ))
            
            fg_history_plot["7_day_ma"] = fg_history_plot["value"].rolling(window=7).mean()
            if not fg_history_plot["7_day_ma"].isna().all():
                fig_fg.add_trace(go.Scatter(
                    x=fg_history_plot["dt"],
                    y=fg_history_plot["7_day_ma"],
                    mode="lines",
                    name="7-Day Moving Avg",
                    line=dict(color="#58a6ff", width=2, dash="dash")
                ))
                
            fig_fg.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=True, gridcolor="#21262d", title="Date", color="#c9d1d9"),
                yaxis=dict(showgrid=True, gridcolor="#21262d", title="Value", range=[0, 100], color="#c9d1d9"),
                legend=dict(font=dict(color="#c9d1d9")),
                margin=dict(l=20, r=20, t=20, b=20),
                height=380
            )
            st.plotly_chart(fig_fg, use_container_width=True)
        else:
            st.info("No historical Fear & Greed data found in Athena.")

    # Chart 2: Top Mentioned Coins (Reddit Social Volume)
    with col2:
        st.subheader(f"🔥 Reddit Sentiment & Mentions (Last {days_to_show} Days)")
        if not reddit_mentions_df.empty:
            recent_reddit = reddit_mentions_df.tail(days_to_show)
            btc_total = int(recent_reddit["btc_mentions"].sum()) if "BTC" in selected_coins else 0
            eth_total = int(recent_reddit["eth_mentions"].sum()) if "ETH" in selected_coins else 0
            sol_total = int(recent_reddit["sol_mentions"].sum()) if "SOL" in selected_coins else 0
            
            mentions_list = []
            if "BTC" in selected_coins: mentions_list.append({"coin": "BTC", "mentions": btc_total})
            if "ETH" in selected_coins: mentions_list.append({"coin": "ETH", "mentions": eth_total})
            if "SOL" in selected_coins: mentions_list.append({"coin": "SOL", "mentions": sol_total})
            
            summed_mentions = pd.DataFrame(mentions_list) if mentions_list else pd.DataFrame(columns=["coin", "mentions"])
            
            if not summed_mentions.empty:
                fig_bar = px.bar(
                    summed_mentions,
                    x="coin",
                    y="mentions",
                    color="coin",
                    color_discrete_map={"BTC": "#ff9900", "ETH": "#8c8cff", "SOL": "#39d353"},
                    labels={"coin": "Crypto Token", "mentions": "Reddit Post Mention Count"}
                )
                fig_bar.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=False, color="#c9d1d9"),
                    yaxis=dict(showgrid=True, gridcolor="#21262d", color="#c9d1d9"),
                    showlegend=False,
                    margin=dict(l=20, r=20, t=20, b=20),
                    height=380
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No selected coins to display in Reddit sentiment chart.")
        else:
            st.info("No Reddit post mentions found in Athena.")

    st.markdown("---")

    # ==========================================
    # CHARTS ROW 2 - BTC CORRELATION
    # ==========================================
    st.subheader(f"📈 Price vs Reddit Activity Correlation (BTC) - Last {days_to_show} Days")
    st.markdown("Analyzing how spikes in social discussions on Reddit align with price movement phases.")

    if not prices_df.empty and not reddit_mentions_df.empty:
        btc_prices = prices_df[prices_df["symbol"] == "btc"].copy()
        btc_prices_grouped = btc_prices.groupby("dt")["price"].mean().reset_index()
        btc_prices_grouped.columns = ["report_date", "avg_price"]
        
        btc_mentions = reddit_mentions_df[["report_date", "btc_mentions"]].copy()
        btc_mentions.columns = ["report_date", "mention_count"]
        
        correlation_df = pd.merge(btc_prices_grouped, btc_mentions, on="report_date", how="left")
        correlation_df["mention_count"] = correlation_df["mention_count"].fillna(0)
        correlation_df = correlation_df.sort_values("report_date").reset_index(drop=True)
        # Filter to only show last N days
        correlation_df = correlation_df.tail(days_to_show)
        
        if not correlation_df.empty:
            fig_corr = go.Figure()
            
            fig_corr.add_trace(go.Scatter(
                x=correlation_df["report_date"],
                y=correlation_df["avg_price"],
                mode="lines+markers",
                name="BTC Average Price ($)",
                line=dict(color="#39d353", width=3),
                yaxis="y1"
            ))
            
            fig_corr.add_trace(go.Bar(
                x=correlation_df["report_date"],
                y=correlation_df["mention_count"],
                name="Reddit Mention Count",
                marker=dict(color="rgba(88, 166, 255, 0.4)"),
                yaxis="y2"
            ))
            
            fig_corr.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=True, gridcolor="#21262d", title="Date", color="#c9d1d9"),
                yaxis1=dict(
                    title=dict(text="BTC Average Price ($)", font=dict(color="#39d353")),
                    tickfont=dict(color="#39d353"),
                    showgrid=True,
                    gridcolor="#21262d",
                    color="#39d353"
                ),
                yaxis2=dict(
                    title=dict(text="Reddit Mentions", font=dict(color="#58a6ff")),
                    tickfont=dict(color="#58a6ff"),
                    overlaying="y",
                    side="right",
                    showgrid=False,
                    color="#58a6ff"
                ),
                legend=dict(x=0.01, y=0.99, font=dict(color="#c9d1d9")),
                margin=dict(l=20, r=20, t=20, b=20),
                height=450
            )
            st.plotly_chart(fig_corr, use_container_width=True)
        else:
            st.info("No pricing or Reddit mention data correlation available.")
    else:
        st.info("Pricing or Reddit data is missing to display correlation.")
