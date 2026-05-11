{{ config(materialized='table') }}

SELECT DISTINCT
    coin_id
FROM {{ ref('stg_coingecko') }}
