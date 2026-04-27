WITH price_changes AS (
    SELECT
        coin_id,
        recorded_at,
        price_usd,

        LAG(price_usd) OVER (
            PARTITION BY coin_id
            ORDER BY recorded_at
        ) AS prev_price

    FROM {{ ref('stg_coingecko') }}
)

SELECT *
FROM price_changes
WHERE prev_price IS NOT NULL
  AND ABS(price_usd - prev_price) / prev_price > 0.5