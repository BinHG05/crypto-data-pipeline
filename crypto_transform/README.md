# dbt Layer

This dbt project transforms raw cryptocurrency data stored in BigQuery into analytics-ready models.

## Models

- `stg_coingecko`: standardizes raw CoinGecko prices
- `stg_reddit`: standardizes Reddit discussion data
- `fct_crypto_daily`: daily mart combining prices and Reddit engagement

## Commands

```bash
dbt run --project-dir crypto_transform --profiles-dir crypto_transform
dbt test --project-dir crypto_transform --profiles-dir crypto_transform
```
