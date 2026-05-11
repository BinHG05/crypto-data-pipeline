SELECT *
FROM {{ ref('stg_coingecko') }}
WHERE recorded_at > CURRENT_TIMESTAMP()