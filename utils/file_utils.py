import json
import os
from datetime import datetime

from utils.logger import get_logger

logger = get_logger(__name__)


def save_json(data, source):
    date_str = datetime.now().strftime("%Y-%m-%d")
    dir_path = f"data/raw/{source}/{date_str}"

    logger.info(f"Ensuring local data directory exists | path={dir_path}")
    os.makedirs(dir_path, exist_ok=True)

    file_path = f"{dir_path}/data.jsonl"

    logger.info(
        "Saving raw records to local file | "
        f"source={source} | records={len(data)} | file={file_path}"
    )

    try:
        with open(file_path, "w") as f:
            for record in data:
                f.write(json.dumps(record) + "\n")
    except OSError as exc:
        logger.error(
            "Failed to save local raw data | "
            f"source={source} | file={file_path} | error={exc}"
        )
        raise

    logger.info(f"Saved local raw data successfully | file={file_path}")
