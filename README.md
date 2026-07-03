# Crypto Data Pipeline

An end-to-end data engineering portfolio project that ingests cryptocurrency
market and community data, stores it in Google Cloud, transforms it with dbt,
orchestrates it with Airflow, monitors data quality, and exposes curated data
for analytics and dashboards.

## Overview

This project demonstrates a practical modern data stack:

- Batch ingestion from CoinGecko (prices & trending), Reddit, and Alternative.me (Fear & Greed Index)
- Realtime BTC trade streaming from Binance
- Raw data storage in local landing zone, GCS, and BigQuery
- Data transformation with dbt on BigQuery (calculating Market Sentiment Score and Price vs Social Correlation)
- Airflow orchestration for batch and monitoring workflows
- Data quality checks for empty inputs, raw load success, mart completeness, and streaming freshness
- Failure alerting through email and Slack
- FastAPI endpoint for lightweight data access
- GitHub Actions CI for code quality and dbt validation

The goal of the project is not only to move data, but to show production-minded
engineering habits: validation, observability, fail-fast behavior, and clean
delivery workflows.

## Business Use Case

The pipeline answers an analytics question:

How can we analyze cryptocurrency price behavior alongside Reddit community discussions and the Fear & Greed Index to extract market sentiment metrics and price-social correlations, while keeping all data pipelines trustworthy?

This supports:

- Daily trend reporting for BTC and ETH
- **Top Trending Coins**: Tracking daily search spikes of trending coins
- **Market Sentiment Score**: A composite metric based on Fear & Greed Index and Reddit community activity
- **Price vs Social Correlation**: Assessing the connection between price momentum and social discussions
- Near-realtime monitoring of BTC trade ingestion freshness
- Portfolio-quality examples of data quality and alerting patterns

## Architecture

An interactive architecture diagram is available in [docs/architecture.md](/d:/crypto-data-pipeline/docs/architecture.md:1).

### Batch Flow

`CoinGecko / Reddit / Fear & Greed -> local JSONL -> GCS raw zone -> BigQuery raw dataset -> dbt staging -> dbt marts (fct_crypto_daily, fct_market_insights)`

### Realtime Flow

`Binance websocket -> BigQuery realtime table -> monitoring DAG -> dashboard / alerting`

### Orchestration Flow

`Airflow DAG -> validation tasks -> load tasks -> dbt run -> dbt test -> mart completeness check -> alert on failure`

## Tech Stack

- Python
- Apache Airflow
- dbt
- BigQuery
- Google Cloud Storage
- FastAPI
- Docker Compose
- GitHub Actions
- Black, isort, flake8

## Key Features

### 1. Batch Ingestion

- `ingestion/coingecko_ingest.py` fetches price snapshots
- `ingestion/reddit_ingest.py` fetches Reddit post metadata
- `ingestion/run_pipeline.py` runs both batch ingestors locally

### 2. Streaming Ingestion

- `ingestion/binance_stream.py` streams BTCUSDT trades into BigQuery
- `dags/streaming_monitor.py` validates freshness on a recurring schedule

### 3. Transformation Layer

dbt models include:

- `stg_coingecko`
- `stg_reddit`
- `dim_coin`
- `dim_date`
- `fct_crypto_daily`

dbt tests cover:

- `not_null`
- `unique`
- `relationships`
- accepted numeric ranges
- latest snapshot completeness for expected coins

### 4. Data Quality and Monitoring

The project includes multiple quality checkpoints:

- Local raw file existence and non-empty validation
- Raw BigQuery table row-count validation after load
- Mart completeness validation for expected daily coin coverage
- Streaming freshness validation for realtime BTC data

Detailed monitoring setup is documented in
[docs/monitoring.md](/d:/crypto-data-pipeline/docs/monitoring.md:1).

### 5. Alerting

Airflow failure callbacks send:

- Email alerts when `ALERT_EMAIL_TO` is configured
- Slack alerts when `SLACK_WEBHOOK_URL` is configured

### 6. API Access

- `api/main.py` exposes a simple FastAPI endpoint for daily crypto mart data

### 7. CI and Code Quality

GitHub Actions validates:

- `black --check`
- `isort --check-only`
- `flake8`
- `dbt deps`
- `dbt parse`
- `dbt run`
- `dbt test`

## Repository Structure

```text
api/                FastAPI service
config/             Shared configuration
crypto_transform/   dbt project
dags/               Airflow DAGs
data/               Local raw landing zone
docs/               Project documentation
ingestion/          Batch and streaming ingestion
utils/              Shared helpers
warehouse/          BigQuery load logic
```

## Pipeline Flow

### Batch DAG: `crypto_pipeline_v2`

Execution order:

1. Fetch CoinGecko data
2. Fetch Reddit data
3. Validate local CoinGecko JSONL is not empty
4. Validate local Reddit JSONL is not empty
5. Upload both sources to GCS
6. Load both sources into BigQuery raw tables
7. Validate raw tables contain rows
8. Run `dbt run`
9. Run `dbt test`
10. Validate the daily mart contains expected rows for the target date

### Streaming Monitor DAG: `btc_streaming_monitor_v1`

Execution purpose:

1. Check the latest `event_time` in the realtime BTC table
2. Fail if the table is empty
3. Fail if no recent records exist inside the freshness window
4. Fail if the newest record is older than the allowed delay

## Environment Variables

Core variables used by this project include:

- `GCP_PROJECT_ID`
- `GCP_LOCATION`
- `GCS_BUCKET_NAME`
- `BQ_RAW_DATASET`
- `BQ_MART_DATASET`
- `BQ_COINGECKO_TABLE`
- `BQ_REDDIT_TABLE`
- `BQ_BTC_REALTIME_TABLE`
- `GOOGLE_APPLICATION_CREDENTIALS`
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

See `.env.example` and [docs/monitoring.md](/d:/crypto-data-pipeline/docs/monitoring.md:1)
for setup details.

## Local Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
pip install black isort flake8 dbt-bigquery
```

### 2. Configure environment

```bash
cp .env.example .env
```

Then fill in your GCP, Airflow SMTP, and optional Slack configuration.

### 3. Run batch ingestion locally

```bash
python ingestion/run_pipeline.py
```

### 4. Load raw data to BigQuery

```bash
python warehouse/load_to_bigquery.py
```

### 5. Run dbt

```bash
dbt deps --project-dir crypto_transform --profiles-dir crypto_transform
dbt run --project-dir crypto_transform --profiles-dir crypto_transform
dbt test --project-dir crypto_transform --profiles-dir crypto_transform
```

### 6. Run Airflow

```bash
docker compose up airflow-init
docker compose up
```

### 7. Run streaming ingestion

```bash
python ingestion/binance_stream.py
```

### 8. Run API

```bash
uvicorn api.main:app --reload
```

## Dashboard

This project is designed to support a dashboard layer on top of BigQuery. A
recommended dashboard improvement guide is available in
[docs/dashboard_enhancement.md](/d:/crypto-data-pipeline/docs/dashboard_enhancement.md:1).

Suggested dashboard sections:

- Daily average price by coin
- Reddit post volume by day
- Reddit engagement by day
- Latest BTC streaming freshness indicator
- Daily data completeness / pipeline health indicator

## Interview Storytelling

An interview-ready project narrative is available in
[docs/interview_storytelling.md](/d:/crypto-data-pipeline/docs/interview_storytelling.md:1).

It includes:

- concise elevator pitch
- architecture walkthrough
- technical tradeoffs
- failure and recovery story
- likely interview questions and strong answer angles

## CI Workflow

The GitHub Actions workflow is split into:

- `lint`
- `dbt-ci`

This supports:

- fail-fast feedback
- easier debugging
- reproducible checks with pinned tool versions
- pip dependency caching

## Future Improvements

- Add partition-aware incremental dbt models
- Add unit tests for ingestion and utility functions
- Add dashboard screenshots and published report link
- Introduce environment-specific deployment workflows
- Add Terraform or infrastructure-as-code for GCP setup
- Add data contracts or schema version validation

## Why This Project Matters

This repository is more than an ETL demo. It shows how to combine ingestion,
warehousing, transformation, orchestration, monitoring, alerting, CI, and
storytelling into a complete analytics engineering portfolio project.
