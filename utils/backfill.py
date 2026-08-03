"""
Backfill Utility CLI & Strategy Module
Usage:
    docker compose exec -e PYTHONPATH=/opt/airflow airflow-scheduler python /opt/airflow/utils/backfill.py --days 30
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import requests
from config.api_config import FEAR_GREED_API
from utils.file_utils import save_json
from utils.logger import get_logger
from utils.schema_validator import FearGreedRecord, validate_records

logger = get_logger(__name__)


def backfill_fear_greed(days: int = 30):
    """
    Backfill historical Fear & Greed Index records for the past N days.
    """
    logger.info(f"Starting Fear & Greed Index backfill | days={days}")
    params = {"limit": str(days), "format": "json"}

    session = requests.Session()
    session.trust_env = False

    try:
        response = session.get(FEAR_GREED_API["url"], params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("data", []):
            ts = int(item.get("timestamp"))
            dt = datetime.utcfromtimestamp(ts)
            results.append(
                {
                    "value": int(item.get("value")),
                    "value_classification": item.get("value_classification"),
                    "timestamp": ts,
                    "ingestion_date": dt.strftime("%Y-%m-%d"),
                }
            )

        validated = validate_records(results, FearGreedRecord, "FearGreedBackfill")
        save_json(validated, "fear_greed")
        logger.info(
            f"Successfully backfilled {len(validated)} historical Fear & Greed records."
        )

    except Exception as exc:
        logger.error(f"Fear & Greed backfill failed | error={exc}")
        raise


def run_backfill(days: int):
    print("--------------------------------------------------")
    print(f"🔄 EXECUTING HISTORICAL BACKFILL FOR PAST {days} DAYS")
    print("--------------------------------------------------")

    backfill_fear_greed(days)

    print("--------------------------------------------------")
    print("✅ Backfill raw data fetch completed!")
    print("👉 Next step: Run dbt incremental merge command to update fact tables:")
    print(
        '   docker compose exec airflow-scheduler bash -c "cd /opt/airflow/crypto_transform && dbt run --select fct_crypto_daily fct_market_insights"'
    )
    print("--------------------------------------------------")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Data Pipeline Backfill Utility")
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of past days to backfill (default: 30)",
    )
    args = parser.parse_args()

    run_backfill(args.days)
