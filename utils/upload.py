from pathlib import Path

from google.cloud import storage

from utils.logger import get_logger

logger = get_logger(__name__)


def upload_to_gcs(bucket_name, source_file, destination_blob):

    source_path = Path(source_file)

    if not source_path.exists():

        logger.error(f"Local file not found: {source_path}")

        raise FileNotFoundError(
            f"Local file not found: {source_path}"
        )

    logger.info(
        f"Starting upload to GCS | file={source_path} | destination={destination_blob}"
    )

    try:

        client = storage.Client()

        bucket = client.bucket(bucket_name)

        blob = bucket.blob(destination_blob)

        blob.upload_from_filename(str(source_path))

        logger.info(
            f"Upload successful | file={source_path} | bucket={bucket_name}"
        )

    except Exception as exc:

        logger.error(
            f"GCS upload failed | file={source_path} | error={exc}"
        )

        raise