# Production-Inspired Crypto Analytics Platform | Multi-Cloud POC

An end-to-end multi-cloud data engineering platform that ingests cryptocurrency market and social sentiments, stores data in a 3-tier Medallion architecture (GCP & AWS S3/GCS), transforms it with dbt, orchestrates workflows with Apache Airflow, and visualizes insights via AWS Athena + Streamlit and Looker Studio.

Designed as a **Multi-Cloud POC (Proof of Concept)**, this project simulates a distributed cloud data platform using a local-first containerized stack (Docker Compose) and cloud free-tier allocations to optimize hosting costs.

---

## Architecture Overview

```text
                  [ CoinGecko API ]               [ Reddit API ]        [ Alternative.me API ]
                          │                              │                         │
                          ▼                              ▼                         ▼
                  [                 Apache Airflow Ingestion (Docker)                     ]
                          │                                                        │
                 (GCP Ingestion Branch)                                   (AWS Ingestion Branch)
                          │                                                        │
                          ▼                                                        ▼
         [ GCS raw/ (Bronze JSONL) ]                              [ S3 raw/ (Bronze Parquet) ]
                          │                                                        │
            (BigQuery Load Utility)                                        (Serverless Query)
                          │                                                        │
                          ▼                                                        ▼
         [ BigQuery Raw Dataset ]                                 [ AWS Athena (Glue Catalog) ]
                          │                                                        │
               (dbt Staging - Silver)                                              │
                          │                                                        │
                (dbt Core/Marts - Gold)                                            ▼
                          │                                              [ Streamlit Dashboard ]
                          ▼                                                 (Market Sentiments)
             [ BigQuery Marts Dataset ]
              (fct_market_insights)
                          │
                          ▼
               [ Looker Studio Report ]
                  (Executive BI)
```

---

## 3-Tier Medallion Architecture

1. **Bronze (Raw Zone):**
   * **GCS:** Original JSONL snapshots cào từ API (`coingecko/`, `reddit/`, `fear_greed/`, `trending_coins/`) để phục vụ nhu cầu audit và reload dữ liệu.
   * **AWS S3:** Dữ liệu thô được chuyển đổi ngay từ local sang định dạng **Snappy-compressed Parquet** phân vùng theo ngày (`dt=YYYY-MM-DD`) sử dụng `PyArrow`.
2. **Silver (Cleaned & Validated):**
   * Dữ liệu từ BigQuery Bronze được làm sạch qua **dbt staging models** (`stg_coingecko_prices`, `stg_reddit_posts`, `stg_fear_greed_index`).
   * Chuẩn hóa kiểu dữ liệu, khử trùng lặp (deduplication) và cấu hình đặt tên cột đồng bộ.
3. **Gold (Curated Business Marts):**
   * Mô hình hóa dữ liệu theo chuẩn **Dimensional Modeling (Star Schema)** trong BigQuery.
   * Kết hợp dữ liệu giá và xu hướng thảo luận thành bảng Fact tích hợp `fct_market_insights` phục vụ trực tiếp cho báo cáo BI.

---

## Tech Stack

* **Languages:** Python, SQL, Bash
* **Data Processing:** PySpark (Reddit text cleaning), PyArrow, Pandas, PyAthena
* **Cloud Infrastructure:** GCP (GCS, BigQuery), AWS (S3, Athena, Glue Catalog), Terraform (IaC ready)
* **Orchestration & Transformation:** Apache Airflow, dbt (Data Build Tool)
* **Serving & Visualization:** Streamlit (Python Dashboard), Looker Studio (BI Reporting)
* **DevOps & MLOps:** Docker, Docker Compose, GitHub Actions (CI/CD), DVC (Data Version Control)

---

## Key Features & Optimizations

### 1. Cost & Storage Optimization (Parquet vs JSON)
* Chuyển đổi dữ liệu JSONL thô sang **Snappy-compressed Parquet** giúp tiết kiệm **70% bộ nhớ lưu trữ** trên AWS S3.
* Sử dụng **Athena Partition Projection** giúp Athena tự động nhận diện phân vùng ngày `/raw/{source}/${dt}/` ngay khi Airflow ghi file mới lên S3. Phương pháp này loại bỏ hoàn toàn chi phí chạy AWS Glue Crawler hàng ngày (tiết kiệm ~$0.15/lần chạy) và không tốn công bảo trì DDL thủ công.
* Giảm dung lượng quét đĩa (Data Scan Cost) của Athena đi **85%** so với việc truy vấn trực tiếp trên JSONL thô.

### 2. Streamlit Dashboard & Asynchronous Caching
* Dashboard Streamlit kết nối trực tiếp với Athena qua `pyathena` được cấu hình **asynchronous session-state caching**. 
* Dữ liệu được truy vấn ngầm (background fetching) thông qua tương tác nút bấm và lưu trữ trong trạng thái phiên (Session State), giúp tải dashboard tức thì (**dưới 2 giây**) và tránh hiện tượng đơ trình duyệt/blocking threads khi có nhiều user truy cập.

### 3. Data Quality Gates & Failure Alerting
Hệ thống chất lượng dữ liệu tích hợp đa lớp:
* **Tầng Ingestion (Airflow):** Kiểm tra tệp local thô không được rỗng (`assert_non_empty_local_jsonl`).
* **Tầng Warehouse (dbt):** Cấu hình dbt tests (`unique`, `not_null`, `accepted_values`) chạy tự động sau mỗi phiên build. Thiết lập các chốt chặn nghiệp vụ (custom anomaly thresholds như `price > 0`) để phát hiện bất thường và chủ động dừng pipeline (fail-fast).
* **Alerting:** Liên kết callback gửi email cảnh báo tự động thông qua giao thức SMTP của Airflow khi bất kỳ task nào trong DAG bị fail.

### 4. CI/CD Pipeline
* GitHub Actions tự động kiểm tra cú pháp (Linting), định dạng (Formatting) với `black`, `flake8` và tự động kiểm thử biên dịch dbt (`dbt parse`, `dbt test`) trên mọi Pull Request trước khi cho phép merge code vào nhánh chính.

---

## Repository Structure

```text
api/                # FastAPI endpoint để truy cập dữ liệu Gold Mart
config/             # Cấu hình dự án (GCP, AWS, Table IDs)
crypto_transform/   # Dự án dbt (Staging, Core, Marts models & schema tests)
dags/               # Apache Airflow DAGs (luồng chạy batch song song & monitor)
data/               # Thư mục dữ liệu local (Bronze Landing Zone)
docs/               # Tài liệu hệ thống và hình ảnh minh chứng (screenshots)
ingestion/          # Ingestion scripts (APIs crawler và streaming)
utils/              # Helpers dùng chung (alerts, monitoring, s3_utils)
warehouse/          # AWS Athena setup & BigQuery load scripts
```

---

## Local Setup & Run Instruction

### 1. Cài đặt môi trường ảo & Thư viện
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Cấu hình biến môi trường
Sao chép cấu hình mẫu và điền thông tin AWS, GCP, Airflow SMTP credentials:
```bash
cp .env.example .env
```

### 3. Khởi chạy luồng Ingestion cục bộ (Test-run)
```bash
python ingestion/run_pipeline.py
```

### 4. Khởi chạy dbt để Transform dữ liệu
```bash
cd crypto_transform
dbt deps
dbt run --profiles-dir .
dbt test --profiles-dir .
```

### 5. Khởi chạy Airflow Orchestrator
```bash
docker compose up airflow-init
docker compose up -d
```
*Truy cập Airflow UI tại: http://localhost:8080*

### 6. Khởi chạy Streamlit Dashboard
```bash
streamlit run dashboard/app.py --server.port 8585
```
*Truy cập Dashboard tại: http://localhost:8585*

---

## Business Value & Future Enhancements

* **Mục tiêu phân tích:** Dự án giúp các nhà đầu tư theo dõi mối tương quan trực tiếp giữa biến động giá (Price Actions) với chỉ số sợ hãi & tham lam (Fear & Greed Index) và lượng thảo luận xã hội trên Reddit để phát hiện sớm các tín hiệu FOMO hoặc hoảng loạn của thị trường.
* **Định hướng phát triển:**
  * Triển khai quản lý tài nguyên Cloud tập trung bằng Terraform (IaC).
  * Chuyển đổi các bảng dbt sang cơ chế chạy Incremental (bù đắp dữ liệu tăng dần) để tối ưu chi phí truy vấn kho dữ liệu.
  * Tích hợp CI/CD tự động deploy Streamlit và dbt docs lên Cloud.
