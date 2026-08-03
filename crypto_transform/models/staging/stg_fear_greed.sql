{{ config(materialized='view') }}

WITH source_data AS (
    SELECT
        CAST(timestamp AS INT64) AS fng_timestamp,
        CAST(value AS INT64) AS fng_value,
        value_classification AS fng_classification,
        DATE(TIMESTAMP_SECONDS(CAST(timestamp AS INT64))) AS report_date
    FROM {{ source('crypto_raw', 'fear_greed_index') }}
),

deduplicated AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY report_date
            ORDER BY fng_timestamp DESC
        ) AS row_num
    FROM source_data
)

SELECT
    CAST(report_date AS STRING) AS record_id,
    report_date,
    fng_timestamp,
    fng_value,
    fng_classification
FROM deduplicated
WHERE row_num = 1
