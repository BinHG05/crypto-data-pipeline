SELECT *
FROM {{ ref('stg_coingecko') }}
WHERE price_usd <= 0