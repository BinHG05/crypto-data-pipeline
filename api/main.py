import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from google.cloud import bigquery
from google.cloud.bigquery import QueryJobConfig, ScalarQueryParameter

from config.settings import GCP_PROJECT_ID, MART_DATASET
from utils.logger import get_logger

app = FastAPI(title="Crypto Data API")
logger = get_logger(__name__)

client = bigquery.Client()


@app.get("/")
def read_root():
    return {"message": "Welcome to Crypto Data API. Go to /docs for Swagger UI"}


@app.get("/crypto-daily")
def get_crypto_daily(coin_id: str = "bitcoin"):
    logger.info(f"Received crypto daily request | coin_id={coin_id}")

    query = f"""
        SELECT *
        FROM `{GCP_PROJECT_ID}.{MART_DATASET}.fct_crypto_daily`
        WHERE coin_id = @coin_id
        ORDER BY report_date DESC
        LIMIT 10
    """
    job_config = QueryJobConfig(
        query_parameters=[ScalarQueryParameter("coin_id", "STRING", coin_id)]
    )
    try:
        query_job = client.query(query, job_config=job_config)
        results = query_job.result()
    except Exception as exc:
        logger.error(
            "BigQuery query failed | "
            f"endpoint=/crypto-daily | coin_id={coin_id} | error={exc}"
        )
        raise

    data = []
    for row in results:
        data.append(
            {
                "date": str(row.report_date),
                "coin": row.coin_id,
                "price": row.avg_price,
                "reddit_posts": row.reddit_posts,
                "reddit_score": row.reddit_score,
            }
        )

    logger.info(
        f"Completed crypto daily request | coin_id={coin_id} | rows={len(data)}"
    )

    return data


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True)
