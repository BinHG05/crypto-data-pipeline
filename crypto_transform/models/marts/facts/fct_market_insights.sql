{{ config(
    materialized='incremental',
    unique_key='record_id',
    incremental_strategy='merge',
    partition_by={
        "field": "report_date",
        "data_type": "date"
    },
    cluster_by=["coin_id"]
) }}

WITH daily_prices AS (
    SELECT
        DATE(recorded_at) AS report_date,
        coin_id,
        AVG(price_usd) AS avg_price
    FROM {{ ref('stg_coingecko') }}
    {% if is_incremental() %}
      -- We must fetch the last 7 days of source data + 2 days of lookback = 9 days total (INTERVAL 8 DAY)
      -- to allow the 7-day rolling window averages to compute correctly for the updated dates!
      WHERE DATE(recorded_at) >= (SELECT DATE_SUB(MAX(report_date), INTERVAL 8 DAY) FROM {{ this }})
    {% endif %}
    GROUP BY 1, 2
),

daily_discussions AS (
    SELECT
        report_date,
        COUNT(post_id) AS total_posts,
        SUM(score) AS total_engagement
    FROM {{ ref('stg_reddit') }}
    {% if is_incremental() %}
        WHERE report_date >= (SELECT DATE_SUB(MAX(report_date), INTERVAL 8 DAY) FROM {{ this }})
    {% endif %}
    GROUP BY 1
),

daily_fng AS (
    SELECT
        report_date,
        fng_value,
        fng_classification
    FROM {{ ref('stg_fear_greed') }}
    {% if is_incremental() %}
        WHERE report_date >= (SELECT DATE_SUB(MAX(report_date), INTERVAL 8 DAY) FROM {{ this }})
    {% endif %}
),

daily_trending AS (
    SELECT
        report_date,
        coin_id,
        trending_score
    FROM {{ ref('stg_trending_coins') }}
    {% if is_incremental() %}
        WHERE report_date >= (SELECT DATE_SUB(MAX(report_date), INTERVAL 8 DAY) FROM {{ this }})
    {% endif %}
),

joined AS (
    SELECT
        p.report_date,
        p.coin_id,
        p.avg_price,
        COALESCE(d.total_posts, 0) AS reddit_posts,
        COALESCE(d.total_engagement, 0) AS reddit_engagement,
        COALESCE(f.fng_value, 50) AS fng_value,
        COALESCE(f.fng_classification, 'Neutral') AS fng_classification,
        CASE WHEN t.coin_id IS NOT NULL THEN TRUE ELSE FALSE END AS is_trending,
        COALESCE(t.trending_score, 0) AS trending_score
    FROM daily_prices p
    LEFT JOIN daily_discussions d ON p.report_date = d.report_date
    LEFT JOIN daily_fng f ON p.report_date = f.report_date
    LEFT JOIN daily_trending t ON p.report_date = t.report_date AND p.coin_id = t.coin_id
),

calculated_metrics AS (
    SELECT
        *,
        -- Composite Sentiment Score (0-100): 70% Fear & Greed, 30% Reddit engagement indicator
        -- We cap the Reddit engagement indicator at 100
        CAST(
            ROUND(
                0.7 * fng_value + 
                0.3 * LEAST(100.0, (reddit_posts * 5.0 + reddit_engagement / 10.0))
            ) AS INT64
        ) AS sentiment_score,

        -- 7-day rolling average of price
        AVG(avg_price) OVER (
            PARTITION BY coin_id 
            ORDER BY report_date 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS avg_price_7d,

        -- 7-day rolling average of Reddit posts
        AVG(reddit_posts) OVER (
            PARTITION BY coin_id 
            ORDER BY report_date 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS avg_reddit_posts_7d,

        -- Pearson Correlation between price and reddit posts over a rolling 7-day window
        CORR(avg_price, reddit_posts) OVER (
            PARTITION BY coin_id 
            ORDER BY report_date 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS price_social_corr_7d
    FROM joined
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['coin_id', 'report_date']) }} AS record_id,
    report_date,
    coin_id,
    avg_price,
    reddit_posts,
    reddit_engagement,
    fng_value,
    fng_classification,
    is_trending,
    trending_score,
    sentiment_score,
    avg_price_7d,
    avg_reddit_posts_7d,
    COALESCE(price_social_corr_7d, 0.0) AS price_social_corr_7d
FROM calculated_metrics
{% if is_incremental() %}
  -- Filter to only insert the newly calculated day(s) into the target table
  WHERE report_date >= (SELECT MAX(report_date) FROM {{ this }})
{% endif %}
