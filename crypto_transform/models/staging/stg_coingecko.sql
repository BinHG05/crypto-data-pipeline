{{ config(materialized='view') }}

WITH source_data AS (
    SELECT
        LOWER(symbol) AS coin_id,
        CAST(price AS FLOAT64) AS price_usd,
        CAST(timestamp AS TIMESTAMP) AS recorded_at,
        CONCAT(
            LOWER(symbol),
            '_',
            CAST(CAST(timestamp AS TIMESTAMP) AS STRING)
        ) AS record_id
    FROM {{ source('crypto_raw', 'coingecko_prices') }}
),

deduplicated AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY record_id
            ORDER BY recorded_at DESC, price_usd DESC
        ) AS row_num
    FROM source_data
)

SELECT
    record_id,
    coin_id,
    price_usd,
    recorded_at
FROM deduplicated
WHERE row_num = 1
