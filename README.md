# Crypto Data Pipeline

End-to-end learning project for data engineering on GCP using batch ingestion, streaming ingestion, orchestration, warehousing, transformation, and BI reporting.

## What This Project Covers

- Python ingestion from CoinGecko and Reddit
- Raw data storage in local landing zone and Google Cloud Storage
- Batch loading from GCS into BigQuery raw tables
- Realtime BTC trade streaming from Binance into BigQuery
- Monitoring for empty daily data, missing daily mart data, and delayed streaming data
- Airflow failure alerts via email and Slack webhook
- dbt staging and mart models on BigQuery
- Airflow orchestration for the batch pipeline
- FastAPI for simple data serving
- Looker Studio dashboard on top of BigQuery

## Architecture

### Batch flow

`CoinGecko / Reddit -> local raw JSONL -> GCS raw zone -> BigQuery raw dataset -> dbt staging/mart`

### Realtime flow

`Binance websocket -> BigQuery realtime table -> Looker Studio dashboard`

## Project Structure

```text
api/                FastAPI service
config/             Shared project settings
crypto_transform/   dbt project
dags/               Airflow DAGs
data/               Local raw landing zone
ingestion/          Batch and streaming ingestion scripts
utils/              Shared helpers
warehouse/          BigQuery loading logic
```

## Main Components

### 1. Ingestion

- `ingestion/coingecko_ingest.py`: fetches price snapshots
- `ingestion/reddit_ingest.py`: fetches Reddit post metadata
- `ingestion/binance_stream.py`: streams BTCUSDT trades into BigQuery
- `ingestion/run_pipeline.py`: runs both batch ingestors locally

### 2. Storage and Warehouse

- Local raw files are written to `data/raw/{source}/{date}/data.jsonl`
- Raw files are uploaded to GCS under `raw/{source}/{date}/data.jsonl`
- `warehouse/load_to_bigquery.py` loads raw JSONL files from GCS into BigQuery

### 3. Orchestration

`dags/crypto_pipeline.py` orchestrates:

1. batch ingestion
2. local non-empty data validation
3. upload to GCS
4. load to BigQuery raw tables
5. raw table validation
6. dbt run and dbt test
7. daily mart completeness validation

`dags/streaming_monitor.py` monitors delayed streaming in the BTC realtime table.

### 4. Monitoring and Alerting

The project now includes:

- Empty data detection for CoinGecko and Reddit batch inputs
- Missing daily data checks for the `fct_crypto_daily` mart
- Delayed streaming detection for the BTC realtime table
- Airflow failure alerts through email and Slack webhook

Detailed setup and operating steps are documented in [docs/monitoring.md](/abs/path/d:/crypto-data-pipeline/docs/monitoring.md:1).

### 5. Transformation

dbt models:

- `stg_coingecko`
- `stg_reddit`
- `fct_crypto_daily`

Basic dbt tests are included for key columns and latest daily snapshot completeness.

## Environment Variables

You can configure the project with environment variables instead of hardcoding values:

- `GCP_PROJECT_ID`
- `GCP_LOCATION`
- `GCS_BUCKET_NAME`
- `BQ_RAW_DATASET`
- `BQ_MART_DATASET`
- `BQ_COINGECKO_TABLE`
- `BQ_REDDIT_TABLE`
- `BQ_BTC_REALTIME_TABLE`
- `GOOGLE_APPLICATION_CREDENTIALS`
- `DBT_PROJECT_DIR`
- `DBT_PROFILES_DIR`
- `EXPECTED_COIN_IDS`
- `STREAMING_MAX_DELAY_MINUTES`
- `STREAMING_MONITOR_SCHEDULE`
- `ALERT_EMAIL_TO`
- `SLACK_WEBHOOK_URL`
- `AIRFLOW__SMTP__SMTP_HOST`
- `AIRFLOW__SMTP__SMTP_USER`
- `AIRFLOW__SMTP__SMTP_PASSWORD`
- `AIRFLOW__SMTP__SMTP_PORT`
- `AIRFLOW__SMTP__SMTP_MAIL_FROM`

## How To Run

### Local batch ingestion

```bash
python ingestion/run_pipeline.py
```

### Load raw data to BigQuery

```bash
python warehouse/load_to_bigquery.py
```

### Run dbt

```bash
dbt run --project-dir crypto_transform --profiles-dir crypto_transform
dbt test --project-dir crypto_transform --profiles-dir crypto_transform
```

### Run streaming ingestion

```bash
python ingestion/binance_stream.py
```

### Run API

```bash
uvicorn api.main:app --reload
```

### Run Airflow

```bash
docker compose up airflow-init
docker compose up
```

## Current Scope

This repository is a learning-focused project that demonstrates how the stack works end to end. It is not intended to be a production-grade platform yet, but the codebase is organized so it can evolve into a stronger portfolio project.
