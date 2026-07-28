"""
Data Lake Compaction Utility (Small Files Optimizer)
Merges raw JSON files into optimized, compressed Parquet files for fast query performance.
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from utils.logger import get_logger

logger = get_logger(__name__)


def compact_raw_json_to_parquet(raw_dir: str, output_parquet: str) -> None:
    """
    Reads all JSON/JSONL files in raw_dir recursively and compacts them into a single Snappy-compressed Parquet file.
    """
    raw_path = Path(raw_dir)
    if not raw_path.exists():
        logger.warning(f"Raw directory does not exist: {raw_dir}")
        return

    json_files = list(raw_path.rglob("*.json*"))
    if not json_files:
        logger.info(f"No JSON/JSONL files found in {raw_dir} to compact.")
        return

    logger.info(f"Starting compaction for {len(json_files)} files in {raw_dir}")
    dfs = []

    for file_path in json_files:
        try:
            is_jsonl = str(file_path).endswith(".jsonl")
            df = pd.read_json(file_path, lines=is_jsonl)
            dfs.append(df)
        except Exception as exc:
            logger.warning(f"Could not read JSON file {file_path}: {exc}")

    if not dfs:
        logger.warning("No valid data frames read for compaction.")
        return

    combined_df = pd.concat(dfs, ignore_index=True)

    # Ensure output folder exists
    output_path = Path(output_parquet)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save as snappy compressed parquet
    combined_df.to_parquet(output_path, compression="snappy", index=False)
    logger.info(
        f"Compaction completed successfully! Written {len(combined_df)} records to {output_parquet}"
    )


def run_compaction():
    print("--------------------------------------------------")
    print("📦 EXECUTING DATA LAKE COMPACTION OPTIMIZATION")
    print("--------------------------------------------------")

    raw_base = PROJECT_ROOT / "data" / "raw"
    warehouse_base = PROJECT_ROOT / "data" / "warehouse"

    for domain in ["coingecko", "reddit", "fear_greed", "trending_coins"]:
        domain_raw = raw_base / domain
        output_file = warehouse_base / domain / f"compacted_{domain}.parquet"
        compact_raw_json_to_parquet(str(domain_raw), str(output_file))

    print("--------------------------------------------------")
    print("✅ Data Lake Compaction completed successfully!")
    print("--------------------------------------------------")


if __name__ == "__main__":
    run_compaction()
