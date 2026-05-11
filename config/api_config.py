from config.settings import (
    BTC_REALTIME_TABLE,
    COINGECKO_TABLE,
    CREDENTIALS_PATH,
    GCP_LOCATION,
    GCP_PROJECT_ID,
    GCS_BUCKET_NAME,
    MART_DATASET,
    RAW_DATASET,
    REDDIT_TABLE,
    bq_table_id,
)

COINGECKO_API = {
    "url": "https://api.coingecko.com/api/v3/simple/price",
    "params": {
        "ids": "bitcoin,ethereum",
        "vs_currencies": "usd",
    },
}

REDDIT_API = {
    "url": "https://www.reddit.com/r/cryptocurrency/hot.json",
    "params": {
        "limit": 10,
    },
    "headers": {
        "User-Agent": "crypto-data-pipeline",
    },
}

GCP_PROJECT = GCP_PROJECT_ID
GCP_REGION = GCP_LOCATION
BUCKET_NAME = GCS_BUCKET_NAME
RAW_DATASET_NAME = RAW_DATASET
MART_DATASET_NAME = MART_DATASET
GOOGLE_APPLICATION_CREDENTIALS_PATH = CREDENTIALS_PATH

COINGECKO_TABLE_ID = bq_table_id(RAW_DATASET, COINGECKO_TABLE)
REDDIT_TABLE_ID = bq_table_id(RAW_DATASET, REDDIT_TABLE)
BTC_REALTIME_TABLE_ID = bq_table_id(RAW_DATASET, BTC_REALTIME_TABLE)
