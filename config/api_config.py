COINGECKO_API = {
    "url": "https://api.coingecko.com/api/v3/simple/price",
    "params": {
        "ids": "bitcoin,ethereum",
        "vs_currencies": "usd"
    }
}

REDDIT_API = {
    "url": "https://www.reddit.com/r/cryptocurrency/hot.json",
    "params": {
        "limit": 10
    },
    "headers": {
        "User-Agent": "crypto-data-pipeline"
    }
}

BUCKET_NAME = "crypto-data-lake-subin"