# Crypto Data Pipeline: Production Upgrade Roadmap Summary

## 📌 Executive Overview

The **Crypto Data Pipeline** has undergone a comprehensive 8-stage production upgrade, transforming it from a basic data script into an **Enterprise-Grade, Automated, Zero-Cost Data Engineering Pipeline**. 

The architecture enforces strict data quality guarantees, schema drift protection, automated failure alerting, dynamic secret management, CI/CD automated testing gates, idempotent historical backfills, and optimized cloud storage performance.

---

## 🛠️ Detailed Breakdown of the 8 Upgrade Stages

### 1️⃣ Part 1: Incremental ETL & Anti-Data-Loss Idempotency
* **Objective**: Prevent data loss when upstream APIs lag/arrive late, while ensuring zero duplicate records in data marts.
* **Implementation**:
  * Materialized Fact models (`fct_crypto_daily.sql`, `fct_market_insights.sql`) as `incremental` with `incremental_strategy='merge'`.
  * Configured `unique_key='record_id'` generated via `dbt_utils.generate_surrogate_key(['coin_id', 'report_date'])`.
  * Built a **3-day Lookback Window (`INTERVAL 2 DAY`)** for basic facts and a **9-day Lookback Window (`INTERVAL 8 DAY`)** for 7-day rolling metrics to account for late-arriving Reddit posts or Fear & Greed indices without corrupting rolling window metrics.

---

### 2️⃣ Part 2: Data Quality Suite & dbt Testing
* **Objective**: Ensure referential integrity and valid numerical ranges before data reaches production dashboards.
* **Implementation**:
  * Configured 56 automated dbt tests in `crypto_transform/models/schema.yml`.
  * Added `not_null` and `unique` primary key tests across dimension tables (`dim_coin`, `dim_date`).
  * Added `relationships` tests linking `fct_crypto_daily` and `fct_market_insights` to dimension tables.
  * Added `dbt_utils.accepted_range` tests for metrics such as `avg_price`, `fng_value` (0-100), and `sentiment_score`.
  * Tied dbt test execution into Airflow DAG with non-zero exit codes to halt downstream mart updates if quality tests fail.

---

### 3️⃣ Part 3: Schema Drift Guard (Pydantic Data Contract)
* **Objective**: Protect the data warehouse from upstream API schema changes or corrupted data payloads.
* **Implementation**:
  * Built `utils/schema_validator.py` defining Pydantic models (`CoinGeckoRecord`, `RedditRecord`, `FearGreedRecord`, `TrendingCoinRecord`).
  * Integrated `validate_records()` validation gates inside all 4 ingestion modules (`coingecko_ingest.py`, `reddit_ingest.py`, `fear_greed_ingest.py`, `trending_coins_ingest.py`).
  * Implemented the **Quarantine Pattern**: Bad records produce structured warning logs and are isolated, while severe schema corruption halts ingestion before invalid files land in storage.

---

### 4️⃣ Part 4: Real-time Alerting System (Telegram Bot)
* **Objective**: Provide instant notification to data engineers upon pipeline failures without incurring Slack/email costs.
* **Implementation**:
  * Built `utils/alerts.py` featuring `send_failure_alert()` and HTML-formatted Telegram dispatching.
  * Extracted `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` securely from environment settings.
  * Integrated `on_failure_callback: send_failure_alert` into Airflow's `default_args` in `dags/crypto_pipeline.py`.
  * Formatted messages contain DAG ID, Task ID, exception traceback, and direct links to Airflow task logs.

---

### 5️⃣ Part 5: Centralized Secrets Manager & Fallback Layer
* **Objective**: Eliminate hardcoded credentials and prepare for enterprise cloud security while maintaining zero local cost.
* **Implementation**:
  * Created `utils/secrets_manager.py` supporting dynamic secret resolution from **GCP Secret Manager** and **AWS Secrets Manager**.
  * Implemented a zero-cost local fallback to `.env` (`get_secret(name, default)`).
  * Updated `config/settings.py` so all modules dynamically load API keys and database credentials through the unified provider layer.

---

### 6️⃣ Part 6: CI/CD Pipeline & Automated Testing Gates
* **Objective**: Automatically test code quality, schema contracts, and SQL compilation on every Git pull request.
* **Implementation**:
  * Created `.github/workflows/ci.yml` configuring 3 automated GitHub Actions quality gates:
    1. **Code Format & Quality**: Executes `black` and `flake8` for PEP8 compliance.
    2. **Automated Pytest Suite**: Executes `tests/test_pipeline_quality.py` testing Pydantic schema validators, alert builders, and secret fallbacks.
    3. **dbt Parsing**: Runs `dbt parse` to validate SQL Jinja syntax and DAG dependency trees.

---

### 7️⃣ Part 7: Idempotent Historical Backfill Strategy
* **Objective**: Provide reliable historical data backfilling without creating duplicate records or hitting API rate limits.
* **Implementation**:
  * Created `utils/backfill.py` CLI supporting date-range parameterization (`--days N`).
  * Documented Airflow native backfill integration: `airflow dags backfill -s <start_date> -e <end_date> crypto_pipeline_v2`.
  * Combined backfill execution with dbt incremental `--select fct_crypto_daily fct_market_insights` to merge historical ranges seamlessly.

---

### 8️⃣ Part 8: Advanced Performance Tuning & Storage Optimization
* **Objective**: Minimize query costs in BigQuery/Athena and optimize Data Lake file storage.
* **Implementation**:
  * Configured **Date Partitioning (`partition_by={"field": "report_date", "data_type": "date"}`)** on fact tables to reduce query scan costs by >90%.
  * Configured **Clustering (`cluster_by=["coin_id"]`)** to accelerate filtered queries to sub-second speeds.
  * Built `utils/compaction.py` to solve the "Small Files Problem" by compacting raw JSON payloads into Snappy-compressed columnar Parquet files.

---

## 📊 Summary Architecture Diagram

```
[Upstream APIs] ──> [Ingestion + Pydantic Schema Guard] ──> [Raw Data Lake (JSON/Parquet)]
                                                                    │
[Telegram Alert] <── [Airflow DAG (on_failure_callback)] <─────────┤ (dbt Incremental ELT)
                                                                    ▼
[CI/CD GitHub Actions] ──> [Secrets Manager] ──> [BigQuery Fact Marts (Partitioned + Clustered)]
```
