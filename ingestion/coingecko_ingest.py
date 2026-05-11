import sys
from pathlib import Path

from utils.logger import get_logger

logger = get_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datetime import datetime

import requests

from config.api_config import COINGECKO_API
from utils.file_utils import save_json


def transform_coingecko(data):
    result = []
    now = datetime.utcnow()

    for coin, value in data.items():
        result.append(
            {
                "symbol": coin,
                "price": value["usd"],
                "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
                "ingestion_date": now.strftime("%Y-%m-%d"),
            }
        )

    return result


def fetch_coingecko():

    logger.info("Starting CoinGecko ingestion")

    session = requests.Session()
    session.trust_env = False

    try:
        response = session.get(
            COINGECKO_API["url"], params=COINGECKO_API["params"], timeout=30
        )

        logger.info(
            f"CoinGecko API request successful | status_code={response.status_code}"
        )

    except requests.RequestException as exc:
        logger.error(f"Failed to fetch CoinGecko data: {exc}")
        raise RuntimeError(f"Failed to fetch CoinGecko data: {exc}") from exc

    if response.status_code != 200:
        logger.error(f"CoinGecko API failed | status_code={response.status_code}")
        raise Exception(f"API Error: {response.status_code}")

    data = response.json()

    # nested -> flat
    result = transform_coingecko(data)

    logger.info(f"Transformed CoinGecko data successfully | records={len(result)}")

    if not result:
        logger.error("CoinGecko returned empty dataset")
        raise ValueError("CoinGecko returned empty dataset")

    save_json(result, "coingecko")

    logger.info("Saved CoinGecko raw data successfully")


if __name__ == "__main__":
    fetch_coingecko()
