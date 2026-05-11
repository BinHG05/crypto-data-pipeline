{{ config(materialized='table') }}

WITH dates AS (
    SELECT DISTINCT report_date
    FROM {{ ref('fct_crypto_daily') }}
)

SELECT
    report_date AS date,
    EXTRACT(YEAR FROM report_date) AS year,
    EXTRACT(MONTH FROM report_date) AS month,
    EXTRACT(DAY FROM report_date) AS day
FROM dates