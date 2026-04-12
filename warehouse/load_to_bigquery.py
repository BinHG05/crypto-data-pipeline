from google.cloud import bigquery

client = bigquery.Client()

def load_coingecko():
    print("🚀 Starting load job...")

    uri = "gs://crypto-data-lake-subin/raw/coingecko/*/data.jsonl"

    table_id = "snappy-monolith-481115-e5.crypto_dataset.coingecko_prices"

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition="WRITE_APPEND",
    )

    load_job = client.load_table_from_uri(uri, table_id, job_config=job_config)

    load_job.result()

    print("✅ DONE loading data")

if __name__ == "__main__":
    load_coingecko()