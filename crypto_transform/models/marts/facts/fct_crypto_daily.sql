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

WITH prices AS (
    SELECT 
        DATE(recorded_at) AS report_date,
        coin_id,
        AVG(price_usd) AS avg_price
    FROM {{ ref('stg_coingecko') }}
    {% if is_incremental() %}
      -- ✅ Dùng Lookback Window ngắn (3 ngày) để cover lỗi trễ dữ liệu từ nguồn
      WHERE DATE(recorded_at) >= (SELECT DATE_SUB(MAX(report_date), INTERVAL 2 DAY) FROM {{ this }})
    {% endif %}
    GROUP BY 1, 2
),

discussions AS (
    SELECT 
        report_date,
        COUNT(post_id) AS total_posts,
        SUM(score) AS total_engagement
    FROM {{ ref('stg_reddit') }}
    {% if is_incremental() %}
      -- ✅ Đồng bộ khoảng thời gian lookback với nhánh prices
      WHERE report_date >= (SELECT DATE_SUB(MAX(report_date), INTERVAL 2 DAY) FROM {{ this }})
    {% endif %}
    GROUP BY 1
),

joined_data AS (
    SELECT 
        p.report_date,
        p.coin_id,
        p.avg_price,
        COALESCE(d.total_posts, 0) AS reddit_posts,
        COALESCE(d.total_engagement, 0) AS reddit_score
    FROM prices p
    LEFT JOIN discussions d 
        ON p.report_date = d.report_date
)

-- ✅ Tầng SELECT cuối cùng sạch sẽ, tường minh, sinh Surrogate Key chuẩn cú pháp
SELECT 
    {{ dbt_utils.generate_surrogate_key(['coin_id', 'report_date']) }} AS record_id,
    report_date,
    coin_id,
    avg_price,
    reddit_posts,
    reddit_score
FROM joined_data