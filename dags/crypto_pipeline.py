import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.exceptions import AirflowException, AirflowSkipException
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

logger = logging.getLogger(__name__)

sys.path.append("/opt/airflow")

from config.api_config import BUCKET_NAME
from config.settings import ALERT_EMAIL_TO
from ingestion.coingecko_ingest import fetch_coingecko
from ingestion.fear_greed_ingest import fetch_fear_greed
from ingestion.reddit_ingest import fetch_reddit
from ingestion.trending_coins_ingest import fetch_trending_coins
from utils.alerts import send_failure_alert
from utils.monitoring import (
    RAW_TABLES,
    assert_expected_daily_mart_rows,
    assert_non_empty_local_jsonl,
    assert_raw_table_has_rows_for_source,
)
from utils.upload import upload_to_gcs
from warehouse.load_to_bigquery import load_all

default_args = {
    "owner": "dat",
    "start_date": datetime(2024, 1, 1),
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(minutes=15),
    "email": ALERT_EMAIL_TO,
    "email_on_failure": bool(ALERT_EMAIL_TO),
    "on_failure_callback": send_failure_alert,
}


def upload_source_to_gcs(source: str) -> None:

    today = datetime.utcnow().strftime("%Y-%m-%d")

    local_file = Path(f"/opt/airflow/data/raw/{source}/{today}/data.jsonl")

    if not local_file.exists():

        logger.warning(f"No local file found for {source}")

        raise AirflowSkipException(f"No data for {source}")

    logger.info(f"Uploading {source} data to GCS")

    upload_to_gcs(BUCKET_NAME, local_file, f"raw/{source}/{today}/data.jsonl")

    logger.info(f"Upload completed for {source}")


def convert_and_upload_source_to_s3(source: str) -> None:
    from utils.s3_utils import convert_and_upload_to_s3

    today = datetime.utcnow().strftime("%Y-%m-%d")
    local_file = Path(f"/opt/airflow/data/raw/{source}/{today}/data.jsonl")

    if not local_file.exists():
        logger.warning(f"No local file found for S3 upload of {source}")
        raise AirflowSkipException(f"No data for {source}")

    s3_key = f"raw/{source}/{today}/data.parquet"
    logger.info(f"Converting and uploading {source} data to S3 as Parquet")
    convert_and_upload_to_s3(str(local_file), s3_key)
    logger.info(f"S3 Parquet upload completed for {source}")


def validate_local_source_data(source: str) -> None:
    record_count = assert_non_empty_local_jsonl(source)
    if record_count <= 0:
        raise AirflowException(f"Source {source} produced no records")


def validate_loaded_raw_tables() -> None:
    for source, table_name in RAW_TABLES.items():
        assert_raw_table_has_rows_for_source(source, table_name)


with DAG(
    dag_id="crypto_pipeline_v2",
    description="Production-grade crypto ETL pipeline with Airflow, BigQuery, and dbt",
    tags=["crypto", "etl", "bigquery", "dbt"],
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

    fetch_fear_greed_task = PythonOperator(
        task_id="fetch_fear_greed",
        python_callable=fetch_fear_greed,
    )

    fetch_trending_coins_task = PythonOperator(
        task_id="fetch_trending_coins",
        python_callable=fetch_trending_coins,
    )

    validate_coingecko_data_task = PythonOperator(
        task_id="validate_coingecko_local_data",
        python_callable=validate_local_source_data,
        op_args=["coingecko"],
    )

    validate_reddit_data_task = PythonOperator(
        task_id="validate_reddit_local_data",
        python_callable=validate_local_source_data,
        op_args=["reddit"],
    )

    validate_fear_greed_data_task = PythonOperator(
        task_id="validate_fear_greed_local_data",
        python_callable=validate_local_source_data,
        op_args=["fear_greed"],
    )

    validate_trending_coins_data_task = PythonOperator(
        task_id="validate_trending_coins_local_data",
        python_callable=validate_local_source_data,
        op_args=["trending_coins"],
    )

    upload_coingecko_task = PythonOperator(
        task_id="upload_coingecko",
        python_callable=upload_source_to_gcs,
        op_args=["coingecko"],
    )

    upload_coingecko_s3_task = PythonOperator(
        task_id="upload_coingecko_s3",
        python_callable=convert_and_upload_source_to_s3,
        op_args=["coingecko"],
    )

    upload_reddit_task = PythonOperator(
        task_id="upload_reddit",
        python_callable=upload_source_to_gcs,
        op_args=["reddit"],
    )

    upload_reddit_s3_task = PythonOperator(
        task_id="upload_reddit_s3",
        python_callable=convert_and_upload_source_to_s3,
        op_args=["reddit"],
    )

    upload_fear_greed_task = PythonOperator(
        task_id="upload_fear_greed",
        python_callable=upload_source_to_gcs,
        op_args=["fear_greed"],
    )

    upload_fear_greed_s3_task = PythonOperator(
        task_id="upload_fear_greed_s3",
        python_callable=convert_and_upload_source_to_s3,
        op_args=["fear_greed"],
    )

    upload_trending_coins_task = PythonOperator(
        task_id="upload_trending_coins",
        python_callable=upload_source_to_gcs,
        op_args=["trending_coins"],
    )

    upload_trending_coins_s3_task = PythonOperator(
        task_id="upload_trending_coins_s3",
        python_callable=convert_and_upload_source_to_s3,
        op_args=["trending_coins"],
    )

    load_bq_task = PythonOperator(
        task_id="load_bigquery",
        python_callable=load_all,
    )

    validate_loaded_raw_tables_task = PythonOperator(
        task_id="validate_loaded_raw_tables",
        python_callable=validate_loaded_raw_tables,
    )

    dbt_run_task = BashOperator(
        task_id="dbt_run",
        bash_command="""
        cd /opt/airflow/crypto_transform &&
        dbt deps &&
        dbt run --profiles-dir . --fail-fast
        """,
    )

    dbt_test_task = BashOperator(
        task_id="dbt_test",
        bash_command="""
        cd /opt/airflow/crypto_transform &&
        dbt deps &&
        dbt test --profiles-dir . --fail-fast
        """,
    )


    validate_daily_mart_task = PythonOperator(
        task_id="validate_daily_mart_data",
        python_callable=assert_expected_daily_mart_rows,
    )

    fetch_coingecko_task >> validate_coingecko_data_task >> [upload_coingecko_task, upload_coingecko_s3_task]
    fetch_reddit_task >> validate_reddit_data_task >> [upload_reddit_task, upload_reddit_s3_task]
    fetch_fear_greed_task >> validate_fear_greed_data_task >> [upload_fear_greed_task, upload_fear_greed_s3_task]
    fetch_trending_coins_task >> validate_trending_coins_data_task >> [upload_trending_coins_task, upload_trending_coins_s3_task]

    (
        [
            upload_coingecko_task,
            upload_reddit_task,
            upload_fear_greed_task,
            upload_trending_coins_task,
        ]
        >> load_bq_task
    )
    (
        load_bq_task
        >> validate_loaded_raw_tables_task
        >> dbt_run_task
        >> dbt_test_task
        >> validate_daily_mart_task
    )
