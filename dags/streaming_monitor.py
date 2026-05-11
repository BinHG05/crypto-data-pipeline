from datetime import datetime, timedelta
import sys

from airflow import DAG
from airflow.operators.python import PythonOperator

sys.path.append("/opt/airflow")

from config.settings import ALERT_EMAIL_TO, STREAMING_MONITOR_SCHEDULE
from utils.alerts import send_failure_alert
from utils.monitoring import assert_streaming_is_fresh


default_args = {
    "owner": "dat",
    "start_date": datetime(2024, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
    "execution_timeout": timedelta(minutes=5),
    "email": ALERT_EMAIL_TO,
    "email_on_failure": bool(ALERT_EMAIL_TO),
    "on_failure_callback": send_failure_alert,
}


with DAG(
    dag_id="btc_streaming_monitor_v1",
    description="Monitors Binance streaming freshness in BigQuery",
    tags=["crypto", "monitoring", "streaming", "bigquery"],
    default_args=default_args,
    schedule=STREAMING_MONITOR_SCHEDULE,
    catchup=False,
) as dag:
    check_streaming_freshness_task = PythonOperator(
        task_id="check_streaming_freshness",
        python_callable=assert_streaming_is_fresh,
    )
