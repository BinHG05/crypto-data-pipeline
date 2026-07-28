# Interview Storytelling Guide

## 30-Second Elevator Pitch (Giới thiệu nhanh)

> *"Em đã xây dựng một nền tảng phân tích dữ liệu tiền điện tử **Multi-Cloud POC** (GCP & AWS) chạy trên mô hình **Local-first (Docker Compose)**. Hệ thống tự động thu thập thông tin giá coin (CoinGecko), tâm lý thị trường (Alternative.me) và dữ liệu thảo luận (Reddit). Dữ liệu được tổ chức theo kiến trúc **Medallion 3 lớp**: từ dữ liệu Parquet phân vùng trên S3/GCS (Bronze), làm sạch bằng dbt (Silver), đến mô hình hóa Star Schema trong BigQuery (Gold) để phục vụ cho các dashboard phân tích tương quan giữa giá và tâm lý cộng đồng."*

---

## 3-Minute Project Story (Trình bày chi tiết dự án)

Khi người phỏng vấn yêu cầu *"Hãy trình bày chi tiết về dự án này của em"*, hãy nói theo mạch **Problem -> Action -> Result**:

### 1. Bối cảnh & Bài toán (Problem)
* Hầu hết các dự án portfolio của sinh viên chỉ dừng lại ở mức chạy script cào dữ liệu đơn giản hoặc dump thẳng vào database mà không quan tâm đến tính nhất quán, giám sát chất lượng dữ liệu (Data Quality), tối ưu chi phí cloud, hay khả năng tự phục hồi (Fault tolerance) khi chạy thực tế.
* Mục tiêu của em là xây dựng một nền tảng dữ liệu hoàn chỉnh, giải quyết bài toán phân tích mối tương quan giữa biến động giá (Price Action) và tâm lý đám đông (Social Sentiment) một cách đáng tin cậy.

### 2. Hành động kỹ thuật (Action)
Để giải quyết bài toán trên, em đã triển khai hệ thống với các kỹ thuật:
* **Mô hình kiến trúc Lakehouse:** Lưu trữ thô dạng **Parquet** (nén Snappy) phân vùng trên AWS S3 và **JSONL** trên GCP GCS. Em dùng **dbt** làm sạch và mô hình hóa dimensional schema trong BigQuery.
* **Tối ưu hóa chi phí & hiệu năng (Cost & Query Optimization):**
  * Sử dụng **Athena Partition Projection** để tự động nhận dạng phân vùng mới hàng ngày trên S3, loại bỏ hoàn toàn chi phí quét của AWS Glue Crawler ($0.15/lần chạy).
  * Chuyển đổi JSONL sang Parquet giúp tiết kiệm 70% dung lượng lưu trữ trên S3 và giảm 85% chi phí scan dữ liệu khi Athena truy vấn.
* **Quan sát và Kiểm soát Chất lượng (Data Quality Gates):**
  * Tích hợp các task kiểm tra dữ liệu local rỗng trên Airflow trước khi đưa lên cloud.
  * Cấu hình **dbt tests** (`unique`, `not_null`, `accepted_values`) chạy tự động sau khi build.
  * Tự thiết lập chốt chặn nghiệp vụ (`price > 0`), nếu vi phạm, pipeline sẽ dừng ngay lập tức (fail-fast) và gửi mail cảnh báo tự động cho admin.
* **Dashboard mượt mà (Streamlit):** Kết nối Streamlit với Athena bằng PyAthena và cấu hình **asynchronous session-state caching** để các truy vấn không làm nghẽn giao diện, tải biểu đồ tương quan dưới 2 giây.

### 3. Kết quả (Result)
* Hệ thống vận hành ổn định trên local Docker stack, giả lập đầy đủ luồng đi của dữ liệu từ API thô đến bảng Gold Marts cuối cùng.
* Chứng minh khả năng thiết kế hệ thống multi-cloud hiệu năng cao với chi phí duy trì gần như bằng 0 (Free Tier).

---

## Technical Tradeoffs & Design Decisions (Các lựa chọn & Đánh đổi kỹ thuật)

Trong phỏng vấn, nhà tuyển dụng rất thích hỏi về sự lựa chọn công nghệ. Bạn hãy chuẩn bị các ý sau:

### 1. Tại sao dùng Airflow thay vì Cron Job thông thường?
> *"Vì Airflow cung cấp khả năng quản lý phụ thuộc giữa các task (task dependencies), tự động thử lại với thời gian trễ (retries & delay), ghi logs tập trung dễ debug, và có cơ chế cảnh báo qua Email/Slack khi có task bị lỗi. Điều mà Cron Job thông thường rất khó quản lý khi luồng dữ liệu phình to."*

### 2. Tại sao lại dùng cả GCP (BigQuery) và AWS (S3/Athena)?
> *"Đây là một thử nghiệm thực tế (POC) của em về kiến trúc Multi-Cloud. GCP BigQuery cực kỳ mạnh mẽ cho việc chuyển đổi dbt và kết nối Looker Studio. Trong khi đó, AWS S3 kết hợp Athena là giải pháp lưu trữ thô và truy vấn ad-hoc serverless vô cùng rẻ và dễ mở rộng. Việc kết hợp này giúp doanh nghiệp linh hoạt trong việc lựa chọn công cụ tối ưu nhất cho từng tác vụ."*

### 3. Tại sao chọn Athena Partition Projection thay vì chạy Glue Crawler?
> *"Vì dữ liệu của chúng ta phân vùng theo mẫu ngày tháng cố định (`yyyy-MM-dd`). Dùng Partition Projection giúp Athena tự tính ra đường dẫn thư mục mà không cần chạy crawler quét đĩa vật lý trên S3. Cách này giúp loại bỏ hoàn toàn chi phí chạy Crawler (~$0.15/lần chạy) và đảm bảo dữ liệu mới xuất hiện là có thể truy vấn ngay tức thì."*

---

## Câu hỏi phỏng vấn dự kiến & Cách trả lời thông minh

### 1. "Em làm thế nào để đảm bảo dữ liệu trên dashboard là đáng tin cậy?"
* **Trả lời:** *"Dữ liệu được kiểm chứng qua 3 lớp phòng vệ (Quality Gates): Đầu tiên là validate file local rỗng trước khi load lên cloud. Tiếp theo là kiểm tra số lượng bản ghi được load vào BigQuery raw. Cuối cùng là chạy dbt tests để kiểm tra khóa chính (unique, not_null) và các ngưỡng nghiệp vụ bất thường. Bất kỳ lỗi nào ở 3 lớp này đều kích hoạt dừng khẩn cấp và báo mail ngay."*

### 2. "Nếu API nguồn thay đổi schema (như CoinGecko thay đổi tên trường), pipeline của em sẽ xử lý thế nào?"
* **Trả lời:** *"Nhờ kiến trúc Medallion, dữ liệu thô vẫn sẽ được lưu an toàn tại tầng Bronze. Khi dbt staging (Silver) chạy kiểm thử `not_null` hoặc `unique` trên schema mới, nó sẽ phát hiện ra sự bất thường và báo lỗi ngay lập tức. Em chỉ cần sửa lại mapping trong dbt staging model mà không cần phải cào lại hay mất dữ liệu lịch sử ở tầng Bronze."*

### 3. "Nếu dự án này được đưa vào production thực tế cho doanh nghiệp lớn, em sẽ nâng cấp những gì?"
* **Trả lời:** *"Em sẽ tập trung vào 3 điểm: Thứ nhất, sử dụng **Terraform** để quản lý và cấu hình toàn bộ tài nguyên AWS/GCP tự động. Thứ hai, chuyển các dbt models sang dạng **Incremental** để chỉ xử lý dữ liệu mới trong ngày thay vì chạy lại toàn bộ bảng lịch sử (giảm chi phí BigQuery). Thứ ba, nâng cấp luồng streaming từ Binance sử dụng Apache Kafka để xử lý realtime quy mô lớn hơn."*
