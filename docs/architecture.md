# 🏛️ End-to-End Enterprise System Architecture

[![Live Streamlit Dashboard](https://img.shields.io/badge/Live_Dashboard-Streamlit_Cloud-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://crypto-data-pipeline-binhg.streamlit.app/)

This document details the production-grade end-to-end data architecture for the **Crypto Data Pipeline & Market Intelligence Platform**.

---

## 📐 Full Architecture Diagram

```mermaid
flowchart TD
    subgraph Sources ["🌐 Upstream Data Sources"]
        CG_Price["CoinGecko Simple Price API"]
        CG_Trend["CoinGecko Trending Coins API"]
        Reddit["Reddit /r/CryptoCurrency API"]
        FNG["Alternative.me Fear & Greed API"]
    end

    subgraph Ingestion ["🛡️ Ingestion & Data Contract Layer"]
        CG_Ingest["coingecko_ingest.py"]
        Reddit_Ingest["reddit_ingest.py"]
        FNG_Ingest["fear_greed_ingest.py"]
        Trend_Ingest["trending_coins_ingest.py"]
        PYD["Pydantic Data Contracts (schema_validator.py)"]
    end

    subgraph Storage ["📦 Data Lake & Storage Layer"]
        RAW_JSON["Bronze Raw Storage (JSONL)"]
        COMPACT["Compaction Engine (utils/compaction.py)"]
        S3["AWS S3 Bucket & Athena Partition Projection"]
    end

    subgraph Warehouse ["🧱 Enterprise Data Warehouse (BigQuery)"]
        STG["Silver Staging Models (dbt views)"]
        DIM["Dimensions (dim_coin, dim_date)"]
        FACT["Gold Fact Marts (fct_market_insights, fct_crypto_daily)"]
        PART["Date Partitioning & Symbol Clustering"]
    end

    subgraph Ops ["⚙️ Orchestration & Operations"]
        Airflow["Apache Airflow 3.x (Celery Executor)"]
        Telegram["Telegram Bot Failure Alerts (utils/alerts.py)"]
        Secrets["Secrets Manager Provider (utils/secrets_manager.py)"]
        CICD["GitHub Actions CI/CD Quality Gates"]
    end

    subgraph Serving ["📊 Serving & Live Visualization"]
        Athena["AWS Athena Serverless Query Engine"]
        Streamlit["Streamlit Community Cloud (Live 24/7 Portal)"]
    end

    CG_Price --> CG_Ingest --> PYD
    CG_Trend --> Trend_Ingest --> PYD
    Reddit --> Reddit_Ingest --> PYD
    FNG --> FNG_Ingest --> PYD

    PYD --> RAW_JSON --> COMPACT --> S3
    RAW_JSON --> STG --> FACT --> PART

    Airflow --> CG_Ingest
    Airflow --> Reddit_Ingest
    Airflow --> FNG_Ingest
    Airflow --> STG
    Airflow --> Telegram

    Secrets --> Ingestion
    Secrets --> Warehouse
    CICD --> Airflow

    S3 --> Athena --> Streamlit
```

---

## 💎 Data Layer Specifications

### 1. Bronze Layer (Raw Data Lake)
* **Format**: Original `.jsonl` files stored under `data/raw/{source}/{dt}/`.
* **Compaction**: `utils/compaction.py` merges small JSON files into compressed, columnar **Snappy Parquet** files to eliminate small-file read overhead.
* **AWS S3 Integration**: Automatically synced to S3 buckets with Athena Partition Projection.

### 2. Silver Layer (Cleaned & Standardized dbt Staging)
* **Models**: `stg_coingecko`, `stg_reddit`, `stg_fear_greed`, `stg_trending_coins`.
* **Transformations**: Type casting, timestamp standardization (UTC), text sanitization, surrogate key generation.

### 3. Gold Layer (Curated Business Marts)
* **Models**: `fct_crypto_daily`, `fct_market_insights`.
* **Optimizations**: 
  * **Date Partitioning**: `partition_by={"field": "report_date", "data_type": "date"}`.
  * **Clustering**: `cluster_by=["coin_id"]`.
  * **Idempotency**: `incremental_strategy='merge'`, `unique_key='record_id'`.

---

## 🔗 Live Serving
* **Streamlit Live Portal**: [https://crypto-data-pipeline-binhg.streamlit.app/](https://crypto-data-pipeline-binhg.streamlit.app/)
