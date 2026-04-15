from fastapi import FastAPI
from google.cloud import bigquery
from google.cloud.bigquery import QueryJobConfig, ScalarQueryParameter

from config.settings import GCP_PROJECT_ID, MART_DATASET


app = FastAPI(title="Crypto Data API")

client = bigquery.Client()


@app.get("/")
def read_root():
    return {"message": "Welcome to Crypto Data API. Go to /docs for Swagger UI"}


@app.get("/crypto-daily")
def get_crypto_daily(coin_id: str = "bitcoin"):
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
    query_job = client.query(query, job_config=job_config)
    results = query_job.result()

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
    return data
