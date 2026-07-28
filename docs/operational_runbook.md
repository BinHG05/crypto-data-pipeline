# Crypto Data Pipeline: Operational Runbook & Daily Execution Guide

## 📖 Overview

This document provides the standard operating procedures (SOP) for running, monitoring, and maintaining the **Crypto Data Pipeline** in production.

---

## ⏰ 1. Daily Automated Schedule & Pipeline Execution

The pipeline is fully automated and orchestrated by **Apache Airflow**.

* **DAG Name**: `crypto_pipeline_v2`
* **Schedule Interval**: `@daily` (Runs automatically every midnight UTC)
* **Execution Flow**:
  1. `fetch_coingecko` / `fetch_reddit` / `fetch_fear_greed` / `fetch_trending_coins` (Parallel raw ingestion + Pydantic schema validation).
  2. `upload_*_s3` (Raw data upload to Cloud Storage / Data Lake).
  3. `dbt_run` (Incremental transformation into BigQuery Fact tables with 3-day lookback).
  4. `dbt_test` (56 automated quality tests).
  5. `notify_success` (Pipeline completion log).

---

## 🚀 2. System Lifecycle Commands

### Starting the Pipeline System
```bash
cd ~/projects/crypto-data-pipeline
docker compose up -d
```

### Checking System Status
```bash
docker compose ps
```

### Restarting Environment (When modifying `.env` or configuration)
```bash
docker compose up -d --force-recreate
```

### Stopping System
```bash
docker compose down
```

---

## 🖥️ 3. Airflow Web UI & Operations

* **Web UI URL**: `http://localhost:8080`
* **Default Credentials**: `airflow` / `airflow`

### Manual Triggering a DAG Run
1. Navigate to DAGs -> `crypto_pipeline_v2`.
2. Click the ▶️ **Trigger DAG** button on top right.

### Re-running a Failed Task
1. Click on the failed (Red) task block in Grid view.
2. Click **Clear** -> Confirm **OK** (Airflow will re-run the task cleanly).

---

## 📱 4. Incident Management & Telegram Alerts

When any task fails, Airflow's `on_failure_callback` fires automatically and sends an HTML alert to your Telegram:

### When an Alert Arrives:
1. Open the Telegram notification to inspect `DAG ID`, `Task ID`, and `Exception`.
2. Open Airflow UI log URL included in the Telegram message.
3. Fix the underlying root cause (e.g. API rate limit or network glitch).
4. On Airflow UI, click **Clear** on the failed task to resume execution.

---

## 🧪 5. Data Quality & Integrity Verification

To run manual data quality tests across all BigQuery models:

```bash
docker compose exec airflow-scheduler bash -c "cd /opt/airflow/crypto_transform && dbt test"
```

To run Python unit tests for schema contracts and alerts:
```bash
docker compose exec -e PYTHONPATH=/opt/airflow airflow-scheduler python -m unittest discover -s /opt/airflow/tests
```

---

## 🔄 6. Historical Data Backfill SOP

If the pipeline was down for several days or historical data needs to be re-populated:

### Step 1: Run Raw Ingestion Backfill
```bash
docker compose exec -e PYTHONPATH=/opt/airflow airflow-scheduler python /opt/airflow/utils/backfill.py --days 30
```

### Step 2: Run dbt Incremental Merge
```bash
docker compose exec airflow-scheduler bash -c "cd /opt/airflow/crypto_transform && dbt run --select fct_crypto_daily fct_market_insights"
```

---

## 📦 7. Data Lake Storage Compaction

To compact small raw JSON payloads into Snappy-compressed columnar Parquet files:

```bash
docker compose exec -e PYTHONPATH=/opt/airflow airflow-scheduler python /opt/airflow/utils/compaction.py
```
