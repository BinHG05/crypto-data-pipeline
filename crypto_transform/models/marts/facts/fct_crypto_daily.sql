{{ config(materialized='table') }}

WITH prices AS (
    SELECT 
        DATE(recorded_at) AS report_date,
        coin_id,
        AVG(price_usd) AS avg_price
    FROM {{ ref('stg_coingecko') }}
    GROUP BY 1, 2
),

discussions AS (
    SELECT 
        report_date,
        COUNT(post_id) AS total_posts,
        SUM(score) AS total_engagement
    FROM {{ ref('stg_reddit') }}
    GROUP BY 1
)

SELECT 
    p.report_date,
    p.coin_id,

    -- ✅ BUSINESS PRIMARY KEY
    CONCAT(p.coin_id, '_', CAST(p.report_date AS STRING)) AS record_id,

    p.avg_price,
    COALESCE(d.total_posts, 0) AS reddit_posts,
    COALESCE(d.total_engagement, 0) AS reddit_score

FROM prices p
LEFT JOIN discussions d 
    ON p.report_date = d.report_date