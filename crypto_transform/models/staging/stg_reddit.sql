{{ config(materialized='view') }}

WITH raw_reddit AS (
    SELECT * FROM {{ source('crypto_raw', 'reddit_posts') }}
),

normalized AS (
    SELECT
        id AS post_id,
        title,
        CAST(score AS INT64) AS score,
        CAST(created_utc AS TIMESTAMP) AS created_at,
        DATE(CAST(created_utc AS TIMESTAMP)) AS report_date
    FROM raw_reddit
),

deduplicated AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY post_id
            ORDER BY created_at DESC, score DESC, title DESC
        ) AS row_num
    FROM normalized
)

SELECT
    post_id AS record_id,
    post_id,
    title,
    score,
    created_at,
    report_date
FROM deduplicated
WHERE row_num = 1
