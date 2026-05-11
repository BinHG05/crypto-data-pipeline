from pathlib import Path
import sys

from utils.logger import get_logger

logger = get_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import requests
from utils.file_utils import save_json
from config.api_config import REDDIT_API


def fetch_reddit():

    logger.info("Starting Reddit ingestion")

    session = requests.Session()
    session.trust_env = False

    try:
        response = session.get(
            REDDIT_API["url"],
            headers=REDDIT_API["headers"],
            params=REDDIT_API["params"],
            timeout=30
        )

        logger.info(
            f"Reddit API request successful | status_code={response.status_code}"
        )

    except requests.RequestException as exc:
        logger.error(f"Failed to fetch Reddit data: {exc}")
        raise RuntimeError(f"Failed to fetch Reddit data: {exc}") from exc

    if response.status_code != 200:

        logger.error(
            f"Reddit API failed | status_code={response.status_code}"
        )

        raise Exception("Reddit API failed")

    raw_data = response.json()

    children = raw_data.get("data", {}).get("children", [])

    posts = []

    for item in children:
        post = item.get("data", {})

        posts.append({
            "id": post.get("id"),
            "title": post.get("title"),
            "score": post.get("score"),
            "created_utc": post.get("created_utc"),
            "url": post.get("url")
        })

    logger.info(
        f"Parsed Reddit posts successfully | posts={len(posts)}"
    )

    if not posts:
        logger.error("Reddit API returned empty dataset")
        raise ValueError("Reddit API returned empty dataset")

    save_json(posts, "reddit")

    logger.info("Saved Reddit raw data successfully")


if __name__ == "__main__":
    fetch_reddit()
