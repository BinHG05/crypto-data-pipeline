from datetime import datetime, timedelta
import logging
from pathlib import Path
import sys

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.exceptions import AirflowSkipException

logger = logging.getLogger(__name__)
sys.path.append("/opt/airflow")

from config.api_config import BUCKET_NAME
from ingestion.coingecko_ingest import fetch_coingecko
from ingestion.reddit_ingest import fetch_reddit
from utils.upload import upload_to_gcs
from warehouse.load_to_bigquery import load_all


default_args = {
    "owner": "dat",
    "start_date": datetime(2024, 1, 1),
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(minutes=15),
}


def upload_source_to_gcs(source: str) -> None:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    local_file = Path(f"/opt/airflow/data/raw/{source}/{today}/data.jsonl")

    if not local_file.exists():
        raise AirflowSkipException(f"No data for {source}")

    logger.info(f"Uploading {source} data...")
    upload_to_gcs(BUCKET_NAME, local_file, f"raw/{source}/{today}/data.jsonl")


with DAG(
    dag_id="crypto_pipeline_v2",
    default_args=default_args,
    schedule="@daily",
    catchup=False,
) as dag:

    fetch_coingecko = PythonOperator(
        task_id="fetch_coingecko",
        python_callable=fetch_coingecko,
    )

    fetch_reddit = PythonOperator(
        task_id="fetch_reddit",
        python_callable=fetch_reddit,
    )

    upload_coingecko = PythonOperator(
        task_id="upload_coingecko",
        python_callable=upload_source_to_gcs,
        op_args=["coingecko"],
    )

    upload_reddit = PythonOperator(
        task_id="upload_reddit",
        python_callable=upload_source_to_gcs,
        op_args=["reddit"],
    )

    load_bq = PythonOperator(
        task_id="load_bigquery",
        python_callable=load_all,
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/airflow/crypto_transform && dbt run",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="cd /opt/airflow/crypto_transform && dbt test",
    )

    fetch_coingecko >> upload_coingecko
    fetch_reddit >> upload_reddit

    [upload_coingecko, upload_reddit] >> load_bq
    load_bq >> dbt_run >> dbt_test
