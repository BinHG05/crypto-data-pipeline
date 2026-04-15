from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import requests
from utils.file_utils import save_json
from config.api_config import COINGECKO_API

from datetime import datetime

def transform_coingecko(data):
    result = []
    now = datetime.utcnow()

    for coin, value in data.items():
        result.append({
            "symbol": coin,
            "price": value["usd"],
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "ingestion_date": now.strftime("%Y-%m-%d")
        })

    return result

def fetch_coingecko():

    session = requests.Session()
    session.trust_env = False

    try:
        response = session.get(COINGECKO_API["url"], params=COINGECKO_API["params"], timeout=30)
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to fetch CoinGecko data: {exc}") from exc

    if response.status_code != 200:
        raise Exception(f"API Error: {response.status_code}")

    data = response.json()
    ## chuyển json từ nestd -> flat
    result = transform_coingecko(data)

    save_json(result, "coingecko")


if __name__ == "__main__":
    fetch_coingecko()
