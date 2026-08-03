import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.coingecko_ingest import fetch_coingecko
from ingestion.fear_greed_ingest import fetch_fear_greed
from ingestion.reddit_ingest import fetch_reddit
from ingestion.trending_coins_ingest import fetch_trending_coins
from utils.logger import get_logger

logger = get_logger(__name__)


def run():
    logger.info("Starting manual ingestion pipeline")

    fetch_coingecko()
    fetch_reddit()
    fetch_fear_greed()
    fetch_trending_coins()

    logger.info("Manual ingestion pipeline completed")


if __name__ == "__main__":
    run()
