# 🛡️ Monitoring, Quality Control & Alerting SOP

This document describes the multi-layered monitoring, data contract validation, and real-time failure alerting architecture for the **Crypto Data Pipeline**.

---

## 🔍 Multi-Layered Quality Controls

### 1. Ingestion Data Contract Validation (Pydantic Schema Drift Guard)
* **Location**: `utils/schema_validator.py`
* **Behavior**: Intercepts raw API responses before landing in raw storage (`data/raw/`).
* **Models**: `CoinGeckoRecord`, `RedditRecord`, `FearGreedRecord`, `TrendingCoinRecord`.
* **Quarantine Pattern**: Corrupted fields are isolated and logged without corrupting raw data stores.

### 2. Enterprise Data Warehouse Quality Suite (56 dbt Tests)
* **Location**: `crypto_transform/models/schema.yml`
* **Behavior**: Runs 56 automated tests on every `dbt test` run.
* **Test Types**:
  * `unique` & `not_null` primary key constraints.
  * `relationships` referential integrity checks between Fact & Dimension tables.
  * `dbt_utils.accepted_range` metrics validation (`fng_value` 0-100, `avg_price` > 0).

---

## 📱 Real-Time Telegram Incident Alerting

When any Airflow task encounters a failure (API timeout, network glitch, database error), Airflow's `on_failure_callback` fires `send_failure_alert()` from `utils/alerts.py`.

### Telegram Notification Schema:
```text
🚨 Airflow Pipeline Task Failure Alert 🚨

DAG: crypto_pipeline_v2
Task: fetch_coingecko
Run ID: scheduled__2026-08-03T00:00:00+00:00
Execution Time: 2026-08-03 00:00:00 UTC

Exception Traceback:
requests.exceptions.HTTPError: 503 Server Error: Service Unavailable

🔗 Airflow Log URL:
http://localhost:8080/log?dag_id=crypto_pipeline_v2&task_id=fetch_coingecko
```

### Environment Settings Required (`.env`):
```env
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=6189997335
```

---

## 🧪 Operational Diagnostics Commands

### Manual Test Telegram Alert Dispatch:
```bash
docker compose exec -e PYTHONPATH=/opt/airflow airflow-scheduler python /opt/airflow/utils/test_telegram.py
```

### Run Pytest Suite for Data Contracts & Alerts:
```bash
docker compose exec -e PYTHONPATH=/opt/airflow airflow-scheduler python -m unittest discover -s /opt/airflow/tests
```

### Run dbt Quality Test Suite:
```bash
docker compose exec airflow-scheduler bash -c "cd /opt/airflow/crypto_transform && dbt test"
```
