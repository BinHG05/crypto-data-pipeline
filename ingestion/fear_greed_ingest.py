import sys
from pathlib import Path

from utils.logger import get_logger

logger = get_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datetime import datetime
import requests

from config.api_config import FEAR_GREED_API
from utils.file_utils import save_json


def transform_fear_greed(data):
    result = []

    for item in data.get("data", []):
        try:
            ts = int(item.get("timestamp"))
            dt = datetime.utcfromtimestamp(ts)
            result.append(
                {
                    "value": int(item.get("value")),
                    "value_classification": item.get("value_classification"),
                    "timestamp": ts,
                    "ingestion_date": dt.strftime("%Y-%m-%d"),
                }
            )
        except (ValueError, TypeError) as e:
            logger.warning(f"Error parsing fear and greed record {item}: {e}")
            continue

    return result


def fetch_fear_greed():
    logger.info("Starting Fear & Greed Index ingestion")

    session = requests.Session()
    session.trust_env = False

    try:
        response = session.get(
            FEAR_GREED_API["url"], params=FEAR_GREED_API["params"], timeout=30
        )
        logger.info(
            f"Fear & Greed API request successful | status_code={response.status_code}"
        )
    except requests.RequestException as exc:
        logger.error(f"Failed to fetch Fear & Greed data: {exc}")
        raise RuntimeError(f"Failed to fetch Fear & Greed data: {exc}") from exc

    if response.status_code != 200:
        logger.error(f"Fear & Greed API failed | status_code={response.status_code}")
        raise Exception(f"API Error: {response.status_code}")

    data = response.json()
    result = transform_fear_greed(data)

    logger.info(f"Transformed Fear & Greed data successfully | records={len(result)}")

    if not result:
        logger.error("Fear & Greed returned empty dataset")
        raise ValueError("Fear & Greed returned empty dataset")

    save_json(result, "fear_greed")
    logger.info("Saved Fear & Greed raw data successfully")


if __name__ == "__main__":
    fetch_fear_greed()
