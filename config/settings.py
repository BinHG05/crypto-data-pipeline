import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def get_env(name: str, default: str) -> str:
    return os.getenv(name, default).strip()


GCP_PROJECT_ID = get_env("GCP_PROJECT_ID", "snappy-monolith-481115-e5")
GCP_LOCATION = get_env("GCP_LOCATION", "asia-southeast1")
GCS_BUCKET_NAME = get_env("GCS_BUCKET_NAME", "crypto-data-lake-subin")

RAW_DATASET = get_env("BQ_RAW_DATASET", "crypto_dataset")
MART_DATASET = get_env("BQ_MART_DATASET", "crypto_marts")
COINGECKO_TABLE = get_env("BQ_COINGECKO_TABLE", "coingecko_prices")
REDDIT_TABLE = get_env("BQ_REDDIT_TABLE", "reddit_posts")
BTC_REALTIME_TABLE = get_env("BQ_BTC_REALTIME_TABLE", "btc_realtime")

CREDENTIALS_PATH = get_env(
    "GOOGLE_APPLICATION_CREDENTIALS",
    str(PROJECT_ROOT / "gcp-key.json"),
)

DBT_PROJECT_DIR = get_env("DBT_PROJECT_DIR", str(PROJECT_ROOT / "crypto_transform"))
DBT_PROFILES_DIR = get_env("DBT_PROFILES_DIR", DBT_PROJECT_DIR)


def bq_table_id(dataset: str, table: str) -> str:
    return f"{GCP_PROJECT_ID}.{dataset}.{table}"
