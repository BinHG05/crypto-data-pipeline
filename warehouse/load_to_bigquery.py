from google.cloud import bigquery

from config.api_config import BUCKET_NAME, COINGECKO_TABLE_ID, REDDIT_TABLE_ID


client = bigquery.Client()


def load_jsonl_from_gcs(gcs_uri: str, table_id: str) -> None:
    print(f"Starting load job from {gcs_uri} to {table_id}...")

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )

    load_job = client.load_table_from_uri(gcs_uri, table_id, job_config=job_config)
    load_job.result()
    print(f"Finished load job for {table_id}")


def load_coingecko() -> None:
    load_jsonl_from_gcs(
        f"gs://{BUCKET_NAME}/raw/coingecko/*/data.jsonl",
        COINGECKO_TABLE_ID,
    )


def load_reddit() -> None:
    load_jsonl_from_gcs(
        f"gs://{BUCKET_NAME}/raw/reddit/*/data.jsonl",
        REDDIT_TABLE_ID,
    )


def load_all() -> None:
    load_coingecko()
    load_reddit()


if __name__ == "__main__":
    load_all()
