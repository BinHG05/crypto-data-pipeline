-- Step 1: Create the Athena database
CREATE DATABASE IF NOT EXISTS crypto_athena;

-- Step 2: Create external table for CoinGecko Prices (with Partition Projection)
CREATE EXTERNAL TABLE IF NOT EXISTS crypto_athena.coingecko_prices (
    symbol STRING,
    price DOUBLE,
    timestamp STRING
)
PARTITIONED BY (dt STRING)
STORED AS PARQUET
LOCATION 's3://crypto-data-lake-hg/raw/coingecko/'
TBLPROPERTIES (
    'projection.enabled' = 'true',
    'projection.dt.type' = 'date', 
    'projection.dt.range' = '2026-01-01,NOW',
    'projection.dt.format' = 'yyyy-MM-dd',
    'projection.dt.interval' = '1',
    'projection.dt.interval.unit' = 'DAYS',
    'storage.location.template' = 's3://crypto-data-lake-hg/raw/coingecko/${dt}/'
);

-- Step 3: Create external table for Reddit Posts (with Partition Projection)
CREATE EXTERNAL TABLE IF NOT EXISTS crypto_athena.reddit_posts (
    id STRING,
    title STRING,
    score BIGINT,
    created_utc STRING,
    url STRING
)
PARTITIONED BY (dt STRING)
STORED AS PARQUET
LOCATION 's3://crypto-data-lake-hg/raw/reddit/'
TBLPROPERTIES (
    'projection.enabled' = 'true',
    'projection.dt.type' = 'date',
    'projection.dt.range' = '2026-01-01,NOW',
    'projection.dt.format' = 'yyyy-MM-dd',
    'projection.dt.interval' = '1',
    'projection.dt.interval.unit' = 'DAYS',
    'storage.location.template' = 's3://crypto-data-lake-hg/raw/reddit/${dt}/'
);

-- Step 4: Create external table for Fear & Greed Index (with Partition Projection)
CREATE EXTERNAL TABLE IF NOT EXISTS crypto_athena.fear_greed_index (
    timestamp STRING,
    value BIGINT,
    value_classification STRING
)
PARTITIONED BY (dt STRING)
STORED AS PARQUET
LOCATION 's3://crypto-data-lake-hg/raw/fear_greed/'
TBLPROPERTIES (
    'projection.enabled' = 'true',
    'projection.dt.type' = 'date',
    'projection.dt.range' = '2026-01-01,NOW',
    'projection.dt.format' = 'yyyy-MM-dd',
    'projection.dt.interval' = '1',
    'projection.dt.interval.unit' = 'DAYS',
    'storage.location.template' = 's3://crypto-data-lake-hg/raw/fear_greed/${dt}/'
);

-- Step 5: Create external table for CoinGecko Trending Coins (with Partition Projection)
CREATE EXTERNAL TABLE IF NOT EXISTS crypto_athena.coingecko_trending (
    coin_id STRING,
    name STRING,
    symbol STRING,
    market_cap_rank BIGINT,
    score BIGINT,
    timestamp STRING
)
PARTITIONED BY (dt STRING)
STORED AS PARQUET
LOCATION 's3://crypto-data-lake-hg/raw/trending_coins/'
TBLPROPERTIES (
    'projection.enabled' = 'true',
    'projection.dt.type' = 'date',
    'projection.dt.range' = '2026-01-01,NOW',
    'projection.dt.format' = 'yyyy-MM-dd',
    'projection.dt.interval' = '1',
    'projection.dt.interval.unit' = 'DAYS',
    'storage.location.template' = 's3://crypto-data-lake-hg/raw/trending_coins/${dt}/'
);
