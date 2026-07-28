import os
import sys
import time
from pathlib import Path
import boto3
from botocore.exceptions import ClientError

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_REGION,
    AWS_S3_BUCKET_NAME,
    AWS_GLUE_ROLE_ARN,
)
from utils.logger import get_logger

logger = get_logger(__name__)

DATABASE_NAME = "crypto_athena"
CRAWLER_NAME = "crypto_s3_crawler"


def get_glue_client():
    """Initializes and returns a boto3 Glue client using credentials or local environment."""
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        logger.info("Initializing Glue client with explicit credentials")
        return boto3.client(
            "glue",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION or "ap-southeast-1",
        )
    else:
        logger.info("Initializing Glue client using default environment credentials")
        return boto3.client("glue", region_name=AWS_REGION or "ap-southeast-1")


def create_or_verify_database(glue_client):
    """Creates the target database in Glue Catalog if it does not exist."""
    logger.info(f"Checking/Creating Glue Catalog Database: {DATABASE_NAME}")
    try:
        glue_client.create_database(
            DatabaseInput={
                "Name": DATABASE_NAME,
                "Description": "Glue Catalog Database for crypto parquet data lake",
            }
        )
        logger.info(f"Database '{DATABASE_NAME}' created successfully.")
    except ClientError as e:
        if e.response["Error"]["Code"] == "AlreadyExistsException":
            logger.info(f"Database '{DATABASE_NAME}' already exists.")
        else:
            logger.error(f"Failed to create database: {e}")
            raise e


def create_or_update_crawler(glue_client):
    """Creates the crawler if it does not exist, or updates it if it does."""
    if not AWS_GLUE_ROLE_ARN or "your_account_id" in AWS_GLUE_ROLE_ARN:
        logger.error("AWS_GLUE_ROLE_ARN is not configured properly in settings or env!")
        print("\n[ERROR] AWS_GLUE_ROLE_ARN variable is missing or using placeholder.")
        print(
            "Please configure a valid AWS_GLUE_ROLE_ARN in your .env file before running."
        )
        sys.exit(1)

    targets = {
        "S3Targets": [
            {"Path": f"s3://{AWS_S3_BUCKET_NAME}/raw/coingecko/"},
            {"Path": f"s3://{AWS_S3_BUCKET_NAME}/raw/reddit/"},
            {"Path": f"s3://{AWS_S3_BUCKET_NAME}/raw/fear_greed/"},
            {"Path": f"s3://{AWS_S3_BUCKET_NAME}/raw/trending_coins/"},
        ]
    }

    logger.info(f"Configuring Glue Crawler '{CRAWLER_NAME}' for S3 targets...")
    try:
        # Check if crawler exists
        glue_client.get_crawler(Name=CRAWLER_NAME)
        logger.info(
            f"Crawler '{CRAWLER_NAME}' already exists. Updating configuration..."
        )

        # Update crawler
        glue_client.update_crawler(
            Name=CRAWLER_NAME,
            Role=AWS_GLUE_ROLE_ARN,
            DatabaseName=DATABASE_NAME,
            Description="Crawler for crypto S3 parquet files (Ingested by Airflow)",
            Targets=targets,
            SchemaChangePolicy={
                "UpdateBehavior": "UPDATE_IN_DATABASE",
                "DeleteBehavior": "DEPRECATE_IN_DATABASE",
            },
        )
        logger.info(f"Crawler '{CRAWLER_NAME}' updated successfully.")
    except ClientError as e:
        if e.response["Error"]["Code"] == "EntityNotFoundException":
            logger.info(f"Crawler '{CRAWLER_NAME}' not found. Creating a new one...")

            # Create crawler
            glue_client.create_crawler(
                Name=CRAWLER_NAME,
                Role=AWS_GLUE_ROLE_ARN,
                DatabaseName=DATABASE_NAME,
                Description="Crawler for crypto S3 parquet files (Ingested by Airflow)",
                Targets=targets,
                SchemaChangePolicy={
                    "UpdateBehavior": "UPDATE_IN_DATABASE",
                    "DeleteBehavior": "DEPRECATE_IN_DATABASE",
                },
                TablePrefix="",
            )
            logger.info(f"Crawler '{CRAWLER_NAME}' created successfully.")
        else:
            logger.error(f"Failed to configure crawler: {e}")
            raise e


def run_crawler_and_wait(glue_client):
    """Triggers the Glue crawler run and monitors status until it is ready again."""
    logger.info(f"Starting Glue Crawler '{CRAWLER_NAME}'...")
    try:
        glue_client.start_crawler(Name=CRAWLER_NAME)
        logger.info("Crawler run triggered successfully.")
    except ClientError as e:
        if e.response["Error"]["Code"] == "CrawlerRunningException":
            logger.warning(f"Crawler '{CRAWLER_NAME}' is already running.")
        else:
            logger.error(f"Failed to start crawler: {e}")
            raise e

    # Poll status
    logger.info("Polling crawler status...")
    print("Waiting for crawler to complete... (This may take 1-3 minutes)")
    while True:
        try:
            response = glue_client.get_crawler(Name=CRAWLER_NAME)
            crawler_state = response["Crawler"]["State"]
            last_run = response["Crawler"].get("LastCrawl", {})
            status = last_run.get("Status", "N/A")

            print(f"Current Crawler State: {crawler_state} | Last Run Status: {status}")

            if crawler_state == "READY":
                print("\n[SUCCESS] Crawler has finished execution!")
                if status == "SUCCEEDED":
                    logger.info("Crawler run succeeded and synchronized metadata!")
                else:
                    logger.warning(f"Crawler completed with status: {status}")
                break

            time.sleep(15)
        except Exception as ex:
            logger.error(f"Error polling crawler status: {ex}")
            time.sleep(10)


def main():
    print(f"--- AWS Glue Catalog Setup ---")
    print(f"Bucket target: s3://{AWS_S3_BUCKET_NAME}/raw/")
    print(f"Glue Database: {DATABASE_NAME}")
    print(f"Glue IAM Role ARN: {AWS_GLUE_ROLE_ARN}")
    print("---------------------------------")

    client = get_glue_client()
    create_or_verify_database(client)
    create_or_update_crawler(client)

    # Prompt option to trigger run
    run_now = (
        input("\nDo you want to run the crawler right now? (y/n): ").strip().lower()
    )
    if run_now == "y":
        run_crawler_and_wait(client)
    else:
        print(
            "\nSetup finished. You can run the crawler manually in AWS Console or call:"
        )
        print(f"aws glue start-crawler --name {CRAWLER_NAME}")


if __name__ == "__main__":
    main()
