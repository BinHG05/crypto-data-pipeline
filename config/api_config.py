from config.settings import (
    BTC_REALTIME_TABLE,
    COINGECKO_TABLE,
    CREDENTIALS_PATH,
    FEAR_GREED_TABLE,
    GCP_LOCATION,
    GCP_PROJECT_ID,
    GCS_BUCKET_NAME,
    MART_DATASET,
    RAW_DATASET,
    REDDIT_TABLE,
    TRENDING_COINS_TABLE,
    bq_table_id,
)

COINGECKO_API = {
    "url": "https://api.coingecko.com/api/v3/simple/price",
    "params": {
        "ids": "bitcoin,ethereum,solana,cardano,ripple,polkadot,avalanche-2,dogecoin",
        "vs_currencies": "usd",
    },
}

COINGECKO_TRENDING_API = {
    "url": "https://api.coingecko.com/api/v3/search/trending",
}

REDDIT_API = {
    "url": "https://www.reddit.com/r/cryptocurrency/hot.json",
    "fallback_urls": [
        "https://www.reddit.com/r/CryptoCurrency/new.json",
        "https://www.reddit.com/r/Bitcoin/hot.json",
    ],
    "params": {
        "limit": 50,
        "raw_json": 1,
    },
    "headers": {
        "Accept": "application/json",
        "User-Agent": "windows:crypto-data-pipeline:v1.0 (by /u/nguyensubins1)",
    },
}

FEAR_GREED_API = {
    "url": "https://api.alternative.me/fng/",
    "params": {
        "limit": 30,
        "format": "json",
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
FEAR_GREED_TABLE_ID = bq_table_id(RAW_DATASET, FEAR_GREED_TABLE)
TRENDING_COINS_TABLE_ID = bq_table_id(RAW_DATASET, TRENDING_COINS_TABLE)
