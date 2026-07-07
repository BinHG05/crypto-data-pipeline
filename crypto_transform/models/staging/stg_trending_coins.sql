{{ config(materialized='view') }}

WITH source_data AS (
    SELECT
        LOWER(coin_id) AS coin_id,
        name,
        UPPER(symbol) AS symbol,
        CAST(market_cap_rank AS INT64) AS market_cap_rank,
        CAST(score AS INT64) AS trending_score,
        CAST(timestamp AS TIMESTAMP) AS recorded_at,
        DATE(CAST(timestamp AS TIMESTAMP)) AS report_date
    FROM {{ source('crypto_raw', 'coingecko_trending') }}
),

deduplicated AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY coin_id, report_date
            ORDER BY recorded_at DESC
        ) AS row_num
    FROM source_data
)

SELECT
    CONCAT(coin_id, '_', CAST(report_date AS STRING)) AS record_id,
    coin_id,
    name,
    symbol,
    market_cap_rank,
    trending_score,
    recorded_at,
    report_date
FROM deduplicated
WHERE row_num = 1
