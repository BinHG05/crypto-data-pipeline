from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from google.cloud import bigquery

from config.settings import (
    BTC_REALTIME_TABLE,
    COINGECKO_TABLE,
    EXPECTED_COIN_IDS,
    GCP_PROJECT_ID,
    MART_DATASET,
    RAW_DATASET,
    REDDIT_TABLE,
    STREAMING_MAX_DELAY_MINUTES,
)
from utils.logger import get_logger

logger = get_logger(__name__)

client = bigquery.Client()


def _resolve_batch_date(date_str: str | None = None) -> str:
    return date_str or datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _count_jsonl_records(file_path: Path) -> int:
    with file_path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def assert_non_empty_local_jsonl(source: str, date_str: str | None = None) -> int:
    batch_date = _resolve_batch_date(date_str)
    file_path = Path(f"/opt/airflow/data/raw/{source}/{batch_date}/data.jsonl")

    logger.info(f"Checking local raw file for emptiness | source={source} | file={file_path}")

    if not file_path.exists():
        raise FileNotFoundError(f"Expected raw file does not exist: {file_path}")

    record_count = _count_jsonl_records(file_path)
    if record_count <= 0:
        raise ValueError(f"Raw file is empty: {file_path}")

    logger.info(
        f"Validated non-empty local raw file successfully | source={source} | records={record_count}"
    )
    return record_count


def assert_expected_daily_mart_rows(date_str: str | None = None) -> None:
    batch_date = _resolve_batch_date(date_str)
    table_id = f"{GCP_PROJECT_ID}.{MART_DATASET}.fct_crypto_daily"

    logger.info(
        f"Checking daily mart completeness | table={table_id} | report_date={batch_date}"
    )

    query = f"""
        SELECT
            COUNT(*) AS row_count,
            COUNT(DISTINCT coin_id) AS distinct_coin_count,
            ARRAY_AGG(DISTINCT coin_id ORDER BY coin_id) AS coin_ids
        FROM `{table_id}`
        WHERE report_date = @report_date
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("report_date", "DATE", batch_date)
        ]
    )
    row = next(client.query(query, job_config=job_config).result())

    actual_coin_ids = list(row.coin_ids or [])
    missing_coins = sorted(set(EXPECTED_COIN_IDS) - set(actual_coin_ids))

    if row.row_count <= 0:
        raise ValueError(
            f"Missing daily mart data for {batch_date} in {table_id}"
        )

    if missing_coins:
        raise ValueError(
            f"Daily mart data incomplete for {batch_date}. Missing coins: {', '.join(missing_coins)}"
        )

    logger.info(
        "Validated daily mart completeness successfully | "
        f"report_date={batch_date} | rows={row.row_count} | coins={','.join(actual_coin_ids)}"
    )


def assert_streaming_is_fresh(max_delay_minutes: int | None = None) -> None:
    delay_minutes = max_delay_minutes or STREAMING_MAX_DELAY_MINUTES
    table_id = f"{GCP_PROJECT_ID}.{RAW_DATASET}.{BTC_REALTIME_TABLE}"

    logger.info(
        f"Checking streaming freshness | table={table_id} | max_delay_minutes={delay_minutes}"
    )

    query = f"""
        SELECT
            MAX(event_time) AS last_event_time,
            COUNTIF(event_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL @delay_minutes MINUTE)) AS recent_row_count
        FROM `{table_id}`
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("delay_minutes", "INT64", delay_minutes)
        ]
    )
    row = next(client.query(query, job_config=job_config).result())

    if row.last_event_time is None:
        raise ValueError(f"Streaming table is empty: {table_id}")

    now = datetime.now(timezone.utc)
    last_event_time = row.last_event_time
    if last_event_time.tzinfo is None:
        last_event_time = last_event_time.replace(tzinfo=timezone.utc)

    age = now - last_event_time
    max_allowed_age = timedelta(minutes=delay_minutes)

    if age > max_allowed_age:
        raise ValueError(
            f"Streaming data delayed. Last event at {last_event_time.isoformat()} UTC, age={age}"
        )

    if row.recent_row_count <= 0:
        raise ValueError(
            f"No streaming rows found in the last {delay_minutes} minutes for {table_id}"
        )

    logger.info(
        "Validated streaming freshness successfully | "
        f"table={table_id} | last_event_time={last_event_time.isoformat()} | recent_rows={row.recent_row_count}"
    )


def assert_raw_table_has_rows_for_source(source: str, table_name: str) -> None:
    table_id = f"{GCP_PROJECT_ID}.{RAW_DATASET}.{table_name}"

    logger.info(f"Checking raw table load result | source={source} | table={table_id}")

    query = f"""
        SELECT COUNT(*) AS row_count
        FROM `{table_id}`
    """
    row = next(client.query(query).result())

    if row.row_count <= 0:
        raise ValueError(f"Loaded raw table is empty for source {source}: {table_id}")

    logger.info(
        f"Validated raw table contains data | source={source} | table={table_id} | rows={row.row_count}"
    )


RAW_TABLES = {
    "coingecko": COINGECKO_TABLE,
    "reddit": REDDIT_TABLE,
}
