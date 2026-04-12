from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import sys
# 👇 add root project
sys.path.append('/opt/airflow')

# Import code của bạn
from utils.upload import upload_to_gcs
from ingestion.coingecko_ingest import fetch_coingecko   # chỉnh path đúng file bạn

from config.api_config import BUCKET_NAME


default_args = {
    'owner': 'dat',
    'start_date': datetime(2024, 1, 1),
    'retries': 1
}


# 👉 function wrapper cho upload (Airflow-friendly)
def upload_task_func():
    today = datetime.today().strftime("%Y-%m-%d")

    local_file = f"/opt/airflow/data/raw/coingecko/{today}/data.jsonl"
    gcs_path = f"raw/coingecko/{today}/data.jsonl"

    upload_to_gcs(BUCKET_NAME, local_file, gcs_path)


with DAG(
    dag_id='crypto_pipeline',   
    default_args=default_args,
    schedule='@daily',
    catchup=False
) as dag:

    fetch_task = PythonOperator(
        task_id='fetch_coingecko',
        python_callable=fetch_coingecko
    )

    upload_task = PythonOperator(
        task_id='upload_gcs',   
        python_callable=upload_task_func
    )

    fetch_task >> upload_task