import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def get_env(name: str, default: str) -> str:
    """Retrieve configuration or secret with fallback support."""
    try:
        from utils.secrets_manager import get_secret

        return get_secret(name, default)
    except ImportError:
        return os.getenv(name, default).strip()


def get_env_list(name: str, default: str) -> list[str]:
    raw_value = get_env(name, default)
    return [item.strip() for item in raw_value.split(",") if item.strip()]


GCP_PROJECT_ID = get_env("GCP_PROJECT_ID", "snappy-monolith-481115-e5")
GCP_LOCATION = get_env("GCP_LOCATION", "asia-southeast1")
GCS_BUCKET_NAME = get_env("GCS_BUCKET_NAME", "crypto-data-lake-subin")

AWS_S3_BUCKET_NAME = get_env("AWS_S3_BUCKET_NAME", "crypto-data-lake-hg")
AWS_ACCESS_KEY_ID = get_env("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = get_env("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION = get_env("AWS_DEFAULT_REGION", "ap-southeast-1")
AWS_GLUE_ROLE_ARN = get_env("AWS_GLUE_ROLE_ARN", "")

RAW_DATASET = get_env("BQ_RAW_DATASET", "crypto_dataset")
MART_DATASET = get_env("BQ_MART_DATASET", "crypto_marts")
COINGECKO_TABLE = get_env("BQ_COINGECKO_TABLE", "coingecko_prices")
REDDIT_TABLE = get_env("BQ_REDDIT_TABLE", "reddit_posts")
BTC_REALTIME_TABLE = get_env("BQ_BTC_REALTIME_TABLE", "btc_realtime")
FEAR_GREED_TABLE = get_env("BQ_FEAR_GREED_TABLE", "fear_greed_index")
TRENDING_COINS_TABLE = get_env("BQ_TRENDING_COINS_TABLE", "coingecko_trending")

CREDENTIALS_PATH = get_env(
    "GOOGLE_APPLICATION_CREDENTIALS",
    str(PROJECT_ROOT / "gcp-key.json"),
)

DBT_PROJECT_DIR = get_env("DBT_PROJECT_DIR", str(PROJECT_ROOT / "crypto_transform"))
DBT_PROFILES_DIR = get_env("DBT_PROFILES_DIR", DBT_PROJECT_DIR)

EXPECTED_COIN_IDS = get_env_list("EXPECTED_COIN_IDS", "bitcoin,ethereum")
STREAMING_MAX_DELAY_MINUTES = int(get_env("STREAMING_MAX_DELAY_MINUTES", "10"))
STREAMING_MONITOR_SCHEDULE = get_env("STREAMING_MONITOR_SCHEDULE", "*/5 * * * *")
ALERT_EMAIL_TO = get_env_list("ALERT_EMAIL_TO", "")
SLACK_WEBHOOK_URL = get_env("SLACK_WEBHOOK_URL", "")
TELEGRAM_BOT_TOKEN = get_env("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = get_env("TELEGRAM_CHAT_ID", "")


def bq_table_id(dataset: str, table: str) -> str:
    return f"{GCP_PROJECT_ID}.{dataset}.{table}"
