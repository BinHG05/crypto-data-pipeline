from fastapi import FastAPI
from google.cloud import bigquery
import os

app = FastAPI(title="Crypto Data API")

# Cấu hình đường dẫn key nếu bạn chạy local ngoài Docker
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "../gcp-key.json"

client = bigquery.Client()

@app.get("/")
def read_root():
    return {"message": "Welcome to Crypto Data API. Go to /docs for Swagger UI"}

@app.get("/crypto-daily")
def get_crypto_daily(coin_id: str = "bitcoin"):
    query = f"""
        SELECT * FROM `snappy-monolith-481115-e5.crypto_marts.fct_crypto_daily`
        WHERE coin_id = '{coin_id}'
        ORDER BY report_date DESC
        LIMIT 10
    """
    query_job = client.query(query)
    results = query_job.result()
    
    data = []
    for row in results:
        data.append({
            "date": str(row.report_date),
            "coin": row.coin_id,
            "price": row.avg_price,
            "reddit_posts": row.reddit_posts,
            "reddit_score": row.reddit_score
        })
    return data