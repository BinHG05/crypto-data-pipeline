SELECT
    LOWER(symbol) AS coin_id,
    CAST(price AS FLOAT64) AS price_usd,
    CAST(timestamp AS TIMESTAMP) AS recorded_at
FROM {{ source('crypto_raw', 'coingecko_prices') }} 