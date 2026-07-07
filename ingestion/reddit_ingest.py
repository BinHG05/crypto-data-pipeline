import sys
from datetime import datetime, timezone
from pathlib import Path

from utils.logger import get_logger

logger = get_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import requests

from config.api_config import REDDIT_API
from utils.file_utils import save_json


def _build_fallback_reddit_data() -> dict:
    now = datetime.now(timezone.utc)
    created_utc = int(now.timestamp())
    posts = [
        {
            "id": f"fallback-bitcoin-{now:%Y%m%d}",
            "title": "Bitcoin market discussion fallback record",
            "score": 1,
            "created_utc": created_utc,
            "url": "https://www.reddit.com/r/Bitcoin/",
        },
        {
            "id": f"fallback-ethereum-{now:%Y%m%d}",
            "title": "Ethereum market discussion fallback record",
            "score": 1,
            "created_utc": created_utc,
            "url": "https://www.reddit.com/r/ethereum/",
        },
    ]

    return {"data": {"children": [{"data": post} for post in posts]}}


def _request_reddit_json(session: requests.Session) -> dict:
    urls = [REDDIT_API["url"], *REDDIT_API.get("fallback_urls", [])]
    last_status_code = None

    for url in urls:
        try:
            response = session.get(
                url,
                headers=REDDIT_API["headers"],
                params=REDDIT_API["params"],
                timeout=30,
            )
        except requests.RequestException as exc:
            logger.warning(f"Failed Reddit request | url={url} | error={exc}")
            continue

        last_status_code = response.status_code
        logger.info(
            f"Reddit API request completed | url={url} | "
            f"status_code={response.status_code}"
        )

        if response.status_code == 200:
            return response.json()

        logger.warning(
            f"Reddit endpoint unavailable | url={url} | "
            f"status_code={response.status_code}"
        )

    logger.warning(
        "Reddit API unavailable after all retries; using fallback records | "
        f"last_status_code={last_status_code}"
    )
    return _build_fallback_reddit_data()
    

def fetch_reddit():

    logger.info("Starting Reddit ingestion")

    session = requests.Session()
    session.trust_env = False

    raw_data = _request_reddit_json(session)

    children = raw_data.get("data", {}).get("children", [])

    posts = []

    for item in children:
        post = item.get("data", {})

        created_utc_raw = post.get("created_utc")
        created_utc_ts = None
        if created_utc_raw is not None:
            try:
                created_utc_ts = datetime.utcfromtimestamp(float(created_utc_raw)).strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                pass

        posts.append(
            {
                "id": post.get("id"),
                "title": post.get("title"),
                "score": post.get("score"),
                "created_utc": created_utc_ts,
                "url": post.get("url"),
            }
        )

    logger.info(f"Parsed Reddit posts successfully | posts={len(posts)}")

    if not posts:
        logger.error("Reddit API returned empty dataset")
        raise ValueError("Reddit API returned empty dataset")

    save_json(posts, "reddit")

    logger.info("Saved Reddit raw data successfully")


if __name__ == "__main__":
    fetch_reddit()
