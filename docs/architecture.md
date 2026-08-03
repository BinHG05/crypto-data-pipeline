# Architecture Diagram & Pipeline Flow

This document details the updated end-to-end data architecture for the Crypto Data Pipeline. It reflects the inclusion of the new analytical datasets (Fear & Greed Index, Trending Coins) alongside the existing CoinGecko and Reddit batch flows, and the Binance live trade stream.

## End-to-End Pipeline Architecture

```mermaid
graph TD
    %% Source Systems
    subgraph Sources [External Sources]
        CG_Price["CoinGecko Price API"]
        CG_Trend["CoinGecko Trending API"]
        Reddit["Reddit /r/cryptocurrency API"]
        FNG["Alternative.me Fear & Greed API"]
        Binance["Binance WebSocket (BTCUSDT)"]
    end

    %% Ingestion Layer
    subgraph Ingest [Ingestion Layer - Python]
        CG_P_Ingest["coingecko_ingest.py"]
        CG_T_Ingest["trending_coins_ingest.py"]
        Reddit_Ingest["reddit_ingest.py"]
        FNG_Ingest["fear_greed_ingest.py"]
        Binance_Stream["binance_stream.py"]
    end

    %% Landing Zone / Storage
    subgraph Storage [Storage Zone - GCS]
        GCS_Raw["GCS Raw Bucket (JSONL)"]
    end

    %% Data Warehouse Raw Tables
    subgraph BQ_Raw [BigQuery Raw Zone]
        BQ_CG_P["coingecko_prices"]
        BQ_CG_T["coingecko_trending"]
        BQ_Reddit["reddit_posts"]
        BQ_FNG["fear_greed_index"]
        BQ_Binance["btc_realtime"]
    end

    %% Transformation Layer (dbt)
    subgraph dbt [Transformation Layer - dbt on BigQuery]
        direction TB
        stg_CG["stg_coingecko (View)"]
        stg_CGT["stg_trending_coins (View)"]
        stg_Reddit["stg_reddit (View)"]
        stg_FNG["stg_fear_greed (View)"]
        
        dim_C["dim_coin"]
        dim_D["dim_date"]
        
        fct_Insight["fct_market_insights (Table)"]
        fct_Daily["fct_crypto_daily (Table)"]
    end

    %% Exposition / Serving Layer
    subgraph Serving [Serving Layer]
        API["FastAPI App (api/main.py)"]
        Dashboard["Dashboard Layer (BI / Visualizations)"]
    end

    %% Orchestration & Quality
    subgraph Orchestration [Orchestration & Quality Control]
        Airflow["Apache Airflow (dags/crypto_pipeline.py)"]
        DQ_Checks["Data Quality Assertions (utils/monitoring.py)"]
    end

    %% Connections
    CG_Price --> CG_P_Ingest
    CG_Trend --> CG_T_Ingest
    Reddit --> Reddit_Ingest
    FNG --> FNG_Ingest
    Binance --> Binance_Stream

    CG_P_Ingest --> GCS_Raw
    CG_T_Ingest --> GCS_Raw
    Reddit_Ingest --> GCS_Raw
    FNG_Ingest --> GCS_Raw
    Binance_Stream --> BQ_Binance

    GCS_Raw --> BQ_CG_P
    GCS_Raw --> BQ_CG_T
    GCS_Raw --> BQ_Reddit
    GCS_Raw --> BQ_FNG

    BQ_CG_P --> stg_CG
    BQ_CG_T --> stg_CGT
    BQ_Reddit --> stg_Reddit
    BQ_FNG --> stg_FNG

    stg_CG --> fct_Insight
    stg_Reddit --> fct_Insight
    stg_FNG --> fct_Insight
    stg_CGT --> fct_Insight

    dim_C --> fct_Insight
    dim_D --> fct_Insight

    stg_CG --> fct_Daily
    stg_Reddit --> fct_Daily

    fct_Insight --> API
    fct_Daily --> API
    BQ_Binance --> Airflow
    
    API --> Dashboard

    %% Orchestration triggers
    Airflow -.-> Ingest
    Airflow -.-> GCS_Raw
    Airflow -.-> BQ_Raw
    Airflow -.-> DQ_Checks
    Airflow -.-> dbt
```

## Detailed Data Flows

### 1. Ingestion Flow (Batch & Stream)
- **Batch Pipeline**: Managed by Airflow on a `@daily` schedule. It fetches raw snapshots, writes them to a local landing zone (`/data/raw/`), validates that they are non-empty, and uploads them to a GCS bucket.
- **Streaming Pipeline**: Runs as a continuous daemon script `binance_stream.py` fetching real-time trade events from Binance and inserting them directly into the BigQuery `btc_realtime` table. A secondary Airflow DAG monitors its freshness.

### 2. Loading Flow
- The batch loader in `load_to_bigquery.py` loads daily GCS JSONL payloads into raw tables in BigQuery using `WRITE_APPEND` mode.

### 3. Transformation Flow (dbt)
- **Staging**: Views are created over raw tables, cleaning up types, renaming columns, and deduplicating records by custom surrogate keys.
- **Marts (Facts & Dimensions)**: 
  - `dim_coin` contains coin properties (e.g., id, symbol, name).
  - `dim_date` is a date dimension table.
  - `fct_crypto_daily` combines CoinGecko daily average prices and Reddit discussion volume.
  - `fct_market_insights` (New) combines coin prices, Reddit metrics, Fear & Greed index values, and trending statuses to calculate composite Sentiment Scores and rolling correlations.

### 4. API & Application Layer
- A FastAPI application query BigQuery marts on-demand to serve daily metrics and correlation insights to external clients or visualization dashboards.

## Chi tiết từng Tầng trong Dự án

### Tầng 1: Nguồn Dữ Liệu (Sources)
*   **CoinGecko Price API**: Trả về snapshot giá hiện tại của BTC và ETH.
*   **CoinGecko Trending API**: Trả về danh sách top các đồng coin đang thịnh hành (được tìm kiếm nhiều nhất).
*   **Reddit API**: Lấy các bài viết nóng hổi từ subreddit `/r/cryptocurrency` để phân tích thảo luận xã hội.
*   **Fear & Greed Index API**: Lấy chỉ số đo lường nỗi sợ hãi và lòng tham của thị trường.
*   **Binance WebSocket**: Streaming giao dịch trực tiếp cặp BTCUSDT theo thời gian thực.

### Tầng 2 & 3: Ingestion & Landing Zone
*   Các script Python thu thập dữ liệu lô lưu trữ tạm thời thành các tệp JSONL tại cục bộ `data/raw/{source}/{date}/data.jsonl`.
*   Airflow chạy tác vụ kiểm tra DQ cơ bản (tệp không rỗng) rồi tải các tệp này lên **Google Cloud Storage (GCS)** làm tầng Data Lake thô.
*   **Binance Stream** chạy độc lập dưới dạng một background daemon kết nối socket và ghi thẳng vào BigQuery.

### Tầng 4 & 5: BigQuery Warehouse & dbt Transformation
*   Dữ liệu từ GCS được nạp vào BigQuery raw bằng script [load_to_bigquery.py](file:///d:/crypto-data-pipeline/warehouse/load_to_bigquery.py) (sử dụng tính năng `autodetect=True` đã sửa).
*   **dbt Staging**: Làm sạch kiểu dữ liệu, chuẩn hóa tên cột và lọc trùng bản ghi (deduplication) sử dụng kỹ thuật `ROW_NUMBER() OVER (...)`.
*   **dbt Dimensions**: Tạo bảng chiều thời gian `dim_date` và chiều coin `dim_coin`.
*   **dbt Marts**:
    *   `fct_crypto_daily`: Tổng hợp giá trung bình và số bài đăng Reddit theo ngày.
    *   `fct_market_insights`: Tạo chỉ số tâm lý tổng hợp (`sentiment_score`), giá trung bình trượt 7 ngày (`avg_price_7d`), và hệ số tương quan rolling 7 ngày (`price_social_corr_7d`).

### Tầng 6: Serving Layer
*   Endpoint FastAPI tại [main.py](file:///d:/crypto-data-pipeline/api/main.py) kết nối BigQuery, cung cấp API phục vụ dữ liệu đã biến đổi cho ứng dụng bên ngoài hoặc Dashboard BI.

### Tầng 7: Orchestration & Data Quality
*   **Airflow** điều khiển toàn bộ luồng công việc từ lúc fetch dữ liệu cho đến khi kiểm tra tính toàn vẹn (DQ) của Data Mart cuối cùng.
*   Bất kỳ bước nào bị thất bại (lỗi API, dữ liệu trống, dbt test thất bại) đều kích hoạt cảnh báo thông qua **Slack Webhook** hoặc **Email**.
