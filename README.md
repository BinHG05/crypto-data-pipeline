# Crypto Data Pipeline

End-to-end learning project for data engineering on GCP using batch ingestion, streaming ingestion, orchestration, warehousing, transformation, and BI reporting.

## What This Project Covers

- Python ingestion from CoinGecko and Reddit
- Raw data storage in local landing zone and Google Cloud Storage
- Batch loading from GCS into BigQuery raw tables
- Realtime BTC trade streaming from Binance into BigQuery
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
2. upload to GCS
3. load to BigQuery raw tables
4. dbt run and dbt test

### 4. Transformation

dbt models:

- `stg_coingecko`
- `stg_reddit`
- `fct_crypto_daily`

Basic dbt tests are included for key columns.

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
