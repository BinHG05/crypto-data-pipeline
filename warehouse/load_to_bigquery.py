from google.cloud import bigquery

from config.api_config import BUCKET_NAME, COINGECKO_TABLE_ID, REDDIT_TABLE_ID
from utils.logger import get_logger

logger = get_logger(__name__)

client = bigquery.Client()


def load_jsonl_from_gcs(gcs_uri: str, table_id: str) -> None:

    logger.info(
        f"Starting BigQuery load job | source={gcs_uri} | destination={table_id}"
    )

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )

    try:

        load_job = client.load_table_from_uri(
            gcs_uri,
            table_id,
            job_config=job_config,
        )

        load_job.result()
        output_rows = getattr(load_job, "output_rows", None)

        if output_rows == 0:
            logger.error(
                "BigQuery load produced zero rows | "
                f"source={gcs_uri} | destination={table_id}"
            )
            raise ValueError(
                f"BigQuery load produced zero rows for destination {table_id}"
            )

        destination_table = client.get_table(table_id)

        logger.info(
            "BigQuery load completed | "
            f"table={table_id} | loaded_rows={output_rows} | "
            f"total_rows={destination_table.num_rows}"
        )

    except Exception as exc:

        logger.error(f"BigQuery load failed | table={table_id} | error={exc}")

        raise


def load_coingecko() -> None:

    logger.info("Loading CoinGecko data into BigQuery")

    load_jsonl_from_gcs(
        f"gs://{BUCKET_NAME}/raw/coingecko/*/data.jsonl",
        COINGECKO_TABLE_ID,
    )


def load_reddit() -> None:

    logger.info("Loading Reddit data into BigQuery")

    load_jsonl_from_gcs(
        f"gs://{BUCKET_NAME}/raw/reddit/*/data.jsonl",
        REDDIT_TABLE_ID,
    )


def load_all() -> None:

    logger.info("Starting warehouse load process")

    load_coingecko()
    load_reddit()

    logger.info("Completed warehouse load process")


if __name__ == "__main__":
    load_all()
