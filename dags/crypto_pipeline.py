from datetime import datetime
from pathlib import Path
import shutil
import subprocess
import sys

from airflow import DAG
from airflow.operators.python import PythonOperator

sys.path.append("/opt/airflow")

from config.api_config import BUCKET_NAME
from ingestion.coingecko_ingest import fetch_coingecko
from ingestion.reddit_ingest import fetch_reddit
from utils.upload import upload_to_gcs
from warehouse.load_to_bigquery import load_all


default_args = {
    "owner": "dat",
    "start_date": datetime(2024, 1, 1),
    "retries": 1,
}


def upload_source_to_gcs(source: str) -> None:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    local_file = Path(f"/opt/airflow/data/raw/{source}/{today}/data.jsonl")
    gcs_path = f"raw/{source}/{today}/data.jsonl"
    upload_to_gcs(BUCKET_NAME, local_file, gcs_path)


def run_dbt_build() -> None:
    dbt_executable = shutil.which("dbt")
    if dbt_executable is None:
        raise RuntimeError("dbt CLI is not installed in the Airflow environment.")

    subprocess.run(
        [
            dbt_executable,
            "run",
            "--project-dir",
            "/opt/airflow/crypto_transform",
            "--profiles-dir",
            "/opt/airflow/crypto_transform",
        ],
        check=True,
    )
    subprocess.run(
        [
            dbt_executable,
            "test",
            "--project-dir",
            "/opt/airflow/crypto_transform",
            "--profiles-dir",
            "/opt/airflow/crypto_transform",
        ],
        check=True,
    )


with DAG(
    dag_id="crypto_pipeline",
    default_args=default_args,
    schedule="@daily",
    catchup=False,
) as dag:
    fetch_coingecko_task = PythonOperator(
        task_id="fetch_coingecko",
        python_callable=fetch_coingecko,
    )

    fetch_reddit_task = PythonOperator(
        task_id="fetch_reddit",
        python_callable=fetch_reddit,
    )

    upload_coingecko_task = PythonOperator(
        task_id="upload_coingecko_to_gcs",
        python_callable=upload_source_to_gcs,
        op_args=["coingecko"],
    )

    upload_reddit_task = PythonOperator(
        task_id="upload_reddit_to_gcs",
        python_callable=upload_source_to_gcs,
        op_args=["reddit"],
    )

    load_raw_to_bigquery_task = PythonOperator(
        task_id="load_raw_to_bigquery",
        python_callable=load_all,
    )

    dbt_build_task = PythonOperator(
        task_id="run_dbt_models",
        python_callable=run_dbt_build,
    )

    fetch_coingecko_task >> upload_coingecko_task
    fetch_reddit_task >> upload_reddit_task
    [upload_coingecko_task, upload_reddit_task] >> load_raw_to_bigquery_task >> dbt_build_task
