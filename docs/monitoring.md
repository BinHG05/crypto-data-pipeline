# Monitoring and Alerting Guide

## What Is Implemented

### 1. Empty Data Detection

The batch DAG now fails early when a source produces no usable records.

- `ingestion/coingecko_ingest.py` raises an error if CoinGecko returns an empty dataset.
- `ingestion/reddit_ingest.py` raises an error if Reddit returns an empty dataset.
- `dags/crypto_pipeline.py` runs `validate_coingecko_local_data` and `validate_reddit_local_data` to ensure the generated JSONL files exist and contain at least one record before uploading to GCS.
- `warehouse/load_to_bigquery.py` raises an error if a BigQuery load job reports zero loaded rows.

### 2. Missing Daily Data Check

The batch DAG validates that the daily mart contains the expected coin rows after dbt finishes.

- `utils/monitoring.py` checks `fct_crypto_daily` for the current UTC batch date.
- The expected coin list comes from `EXPECTED_COIN_IDS`.
- `crypto_transform/tests/test_fct_crypto_daily_latest_snapshot_not_missing.sql` adds a dbt test that verifies the latest snapshot contains every expected coin.

### 3. Delayed Streaming Detection

A dedicated Airflow DAG monitors the realtime table.

- `dags/streaming_monitor.py` runs on `STREAMING_MONITOR_SCHEDULE`.
- `utils/monitoring.py` checks the latest `event_time` in `btc_realtime`.
- The check fails if:
  - the table is empty
  - there are no recent rows inside the configured window
  - the latest event is older than `STREAMING_MAX_DELAY_MINUTES`

## Alerting

Alerts are triggered through a shared Airflow failure callback in `utils/alerts.py`.

- Email alerts are sent when `ALERT_EMAIL_TO` is set and Airflow SMTP settings are configured.
- Slack alerts are sent when `SLACK_WEBHOOK_URL` is set.
- Both batch and streaming monitor DAGs use the same failure callback.

## Required Environment Variables

Add these values to your `.env`:

```env
EXPECTED_COIN_IDS=bitcoin,ethereum
STREAMING_MAX_DELAY_MINUTES=10
STREAMING_MONITOR_SCHEDULE=*/5 * * * *
ALERT_EMAIL_TO=you@example.com
SLACK_WEBHOOK_URL=
AIRFLOW__SMTP__SMTP_HOST=smtp.gmail.com
AIRFLOW__SMTP__SMTP_STARTTLS=True
AIRFLOW__SMTP__SMTP_SSL=False
AIRFLOW__SMTP__SMTP_USER=your_email@example.com
AIRFLOW__SMTP__SMTP_PASSWORD=your_app_password
AIRFLOW__SMTP__SMTP_PORT=587
AIRFLOW__SMTP__SMTP_MAIL_FROM=your_email@example.com
```

## How the DAGs Behave

### Batch DAG

`crypto_pipeline_v2` now runs in this order:

1. Fetch CoinGecko and Reddit data
2. Validate local JSONL files are not empty
3. Upload raw files to GCS
4. Load raw files into BigQuery
5. Validate raw tables contain rows
6. Run `dbt run`
7. Run `dbt test`
8. Validate `fct_crypto_daily` for the expected daily coin coverage

### Streaming Monitor DAG

`btc_streaming_monitor_v1` runs independently from the batch DAG and only checks the freshness of realtime streaming data.

## Recommended Next Steps

1. Fill in `.env` with real SMTP credentials and, optionally, a Slack webhook URL.
2. Restart Airflow so the new environment variables and DAGs are loaded.
3. Trigger `crypto_pipeline_v2` manually once to confirm the new validation tasks pass.
4. Trigger `btc_streaming_monitor_v1` to confirm streaming freshness monitoring works against your realtime table.
