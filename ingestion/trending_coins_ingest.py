import sys
from pathlib import Path

from utils.logger import get_logger

logger = get_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datetime import datetime
import requests

from config.api_config import COINGECKO_TRENDING_API
from utils.file_utils import save_json
from utils.schema_validator import TrendingCoinRecord, validate_records


def transform_trending_coins(data):
    result = []
    now = datetime.utcnow()

    for entry in data.get("coins", []):
        item = entry.get("item", {})
        if not item:
            continue
        try:
            result.append(
                {
                    "coin_id": item.get("id"),
                    "name": item.get("name"),
                    "symbol": item.get("symbol"),
                    "market_cap_rank": item.get("market_cap_rank"),
                    "score": item.get("score"),  # Trending ranking score
                    "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "ingestion_date": now.strftime("%Y-%m-%d"),
                }
            )
        except Exception as e:
            logger.warning(f"Error parsing trending coin record {entry}: {e}")
            continue

    return result


def fetch_trending_coins():
    logger.info("Starting CoinGecko Trending Coins ingestion")

    session = requests.Session()
    session.trust_env = False

    try:
        response = session.get(COINGECKO_TRENDING_API["url"], timeout=30)
        logger.info(
            f"CoinGecko Trending API request successful | status_code={response.status_code}"
        )
    except requests.RequestException as exc:
        logger.error(f"Failed to fetch CoinGecko Trending Coins: {exc}")
        raise RuntimeError(f"Failed to fetch CoinGecko Trending Coins: {exc}") from exc

    if response.status_code != 200:
        logger.error(
            f"CoinGecko Trending API failed | status_code={response.status_code}"
        )
        raise Exception(f"API Error: {response.status_code}")

    data = response.json()
    result = transform_trending_coins(data)

    logger.info(
        f"Transformed CoinGecko Trending data successfully | records={len(result)}"
    )

    if not result:
        logger.error("CoinGecko Trending returned empty dataset")
        raise ValueError("CoinGecko Trending returned empty dataset")

    # Schema Drift Guard: Pydantic Validation Gate
    validated_result = validate_records(result, TrendingCoinRecord, "TrendingCoins")

    save_json(validated_result, "trending_coins")
    logger.info("Saved CoinGecko Trending raw data successfully")


if __name__ == "__main__":
    fetch_trending_coins()
