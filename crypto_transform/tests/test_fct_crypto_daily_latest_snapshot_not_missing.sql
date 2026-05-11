WITH latest_day AS (
    SELECT MAX(report_date) AS report_date
    FROM {{ ref('fct_crypto_daily') }}
),

actual_coins AS (
    SELECT DISTINCT coin_id
    FROM {{ ref('fct_crypto_daily') }}
    WHERE report_date = (SELECT report_date FROM latest_day)
),

expected_coins AS (
    {% set expected_coins = env_var('EXPECTED_COIN_IDS', 'bitcoin,ethereum').split(',') %}
    {% for coin in expected_coins %}
    SELECT '{{ coin.strip() }}' AS coin_id
    {% if not loop.last %}UNION ALL{% endif %}
    {% endfor %}
),

missing_coins AS (
    SELECT e.coin_id
    FROM expected_coins e
    LEFT JOIN actual_coins a
        ON e.coin_id = a.coin_id
    WHERE a.coin_id IS NULL
)

SELECT *
FROM missing_coins
