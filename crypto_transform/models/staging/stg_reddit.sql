{{ config(materialized='view') }}

WITH raw_reddit AS (
    SELECT * FROM {{ source('crypto_raw', 'reddit_posts') }}
)

SELECT
    id AS post_id,
    title,
    score,
    -- Nếu nó đã là TIMESTAMP, chỉ cần lấy chính nó
    created_utc AS created_at,
    -- Ép về kiểu DATE để làm khóa JOIN
    DATE(created_utc) AS report_date
FROM raw_reddit