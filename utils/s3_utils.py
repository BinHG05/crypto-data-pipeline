import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import boto3
import pandas as pd
from botocore.exceptions import ClientError

from config.settings import (
    AWS_ACCESS_KEY_ID,
    AWS_REGION,
    AWS_S3_BUCKET_NAME,
    AWS_SECRET_ACCESS_KEY,
)
from utils.logger import get_logger

logger = get_logger(__name__)


def get_s3_client():
    """Initializes and returns a boto3 S3 client using configured credentials or defaults."""
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        logger.info("Initializing S3 client with explicit credentials")
        return boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION,
        )
    else:
        logger.info("Initializing S3 client using default environment credentials")
        return boto3.client("s3", region_name=AWS_REGION or "ap-southeast-1")


def convert_jsonl_to_parquet(jsonl_path: Path, parquet_path: Path) -> bool:
    """Converts a local JSONL file to a Parquet file."""
    logger.info(
        f"Converting JSONL to Parquet | source={jsonl_path} | target={parquet_path}"
    )
    try:
        jsonl_path = Path(jsonl_path)
        parquet_path = Path(parquet_path)

        if not jsonl_path.exists():
            logger.error(f"Source JSONL file does not exist: {jsonl_path}")
            return False

        # Read JSONL into pandas
        df = pd.read_json(jsonl_path, lines=True)

        if df.empty:
            logger.warning(f"Source JSONL is empty: {jsonl_path}")
            return False

        # Create parent directory for parquet if not exists
        parquet_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to Parquet using pyarrow engine
        df.to_parquet(parquet_path, index=False, engine="pyarrow")
        logger.info(f"Parquet conversion successful | rows={len(df)}")
        return True

    except Exception as e:
        logger.error(f"Failed to convert JSONL to Parquet | error={e}")
        raise e


def upload_parquet_to_s3(
    parquet_path: Path, s3_key: str, bucket_name: str | None = None
) -> None:
    """Uploads a local Parquet file to AWS S3."""
    target_bucket = bucket_name or AWS_S3_BUCKET_NAME
    if not target_bucket:
        logger.error("No S3 bucket name configured.")
        raise ValueError(
            "S3 bucket name must be specified in settings or function call."
        )

    logger.info(
        f"Uploading Parquet to S3 | file={parquet_path} | bucket={target_bucket} | key={s3_key}"
    )

    try:
        parquet_path = Path(parquet_path)
        if not parquet_path.exists():
            logger.error(f"Local Parquet file not found: {parquet_path}")
            raise FileNotFoundError(f"Local Parquet file not found: {parquet_path}")

        s3_client = get_s3_client()
        s3_client.upload_file(str(parquet_path), target_bucket, s3_key)
        logger.info(f"S3 upload successful | bucket={target_bucket} | key={s3_key}")

    except ClientError as ce:
        logger.error(f"AWS S3 ClientError during upload | error={ce}")
        raise ce
    except Exception as e:
        logger.error(f"Unexpected error during S3 upload | error={e}")
        raise e


def convert_and_upload_to_s3(
    jsonl_path: str, s3_key: str, bucket_name: str | None = None
) -> None:
    """Combines conversion and S3 upload into a single process for pipeline integration."""
    json_p = Path(jsonl_path)
    parquet_p = json_p.with_suffix(".parquet")

    # Step 1: Convert
    success = convert_jsonl_to_parquet(json_p, parquet_p)
    if not success:
        raise ValueError(f"Failed to convert JSONL to Parquet for {jsonl_path}")

    # Step 2: Upload
    upload_parquet_to_s3(parquet_p, s3_key, bucket_name)

    # Step 3: Cleanup local parquet temp file
    if parquet_p.exists():
        parquet_p.unlink()
        logger.info(f"Cleaned up local temporary parquet file: {parquet_p}")
