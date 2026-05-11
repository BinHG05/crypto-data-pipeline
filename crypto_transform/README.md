# dbt Layer

This dbt project transforms raw cryptocurrency data stored in BigQuery into analytics-ready models.

## Models

- `stg_coingecko`: standardizes raw CoinGecko prices
- `stg_reddit`: standardizes Reddit discussion data
- `fct_crypto_daily`: daily mart combining prices and Reddit engagement

## Commands

```bash
conda activate multimodal_gnn
dbt debug
dbt run
dbt test
```

If Google authentication suddenly fails with a proxy-related error, check whether `HTTP_PROXY`, `HTTPS_PROXY`, or `ALL_PROXY` is pointing to an invalid local address.
