"""
Pydantic Schema Validation Gate for Data Ingestion (Schema Drift Guard)
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from utils.logger import get_logger

logger = get_logger(__name__)


class CoinGeckoRecord(BaseModel):
    symbol: str = Field(..., min_length=1)
    price: float = Field(..., ge=0.0)
    timestamp: str
    ingestion_date: str


class RedditRecord(BaseModel):
    id: str = Field(..., min_length=1)
    title: Optional[str] = ""
    score: Optional[int] = 0
    created_utc: Optional[str] = None
    url: Optional[str] = ""


class FearGreedRecord(BaseModel):
    value: int = Field(..., ge=0, le=100)
    value_classification: str
    timestamp: Any
    ingestion_date: str


class TrendingCoinRecord(BaseModel):
    coin_id: str = Field(..., min_length=1)
    name: str
    symbol: str
    market_cap_rank: Optional[int] = None
    score: Optional[int] = None
    timestamp: str
    ingestion_date: str


def validate_records(
    records: List[Dict[str, Any]], model_cls: type[BaseModel], source_name: str
) -> List[Dict[str, Any]]:
    """
    Validates a list of dictionaries against a Pydantic schema model.
    Valid records are returned. Invalid records trigger warnings and are quarantined.
    """
    valid_records = []
    quarantined = []

    for idx, item in enumerate(records):
        try:
            validated = model_cls(**item)
            record_dict = (
                validated.model_dump()
                if hasattr(validated, "model_dump")
                else validated.dict()
            )
            valid_records.append(record_dict)
        except Exception as exc:
            logger.warning(
                f"Schema Drift Detected in {source_name} record #{idx} | "
                f"Error: {exc} | Record: {item}"
            )
            quarantined.append(item)

    if quarantined:
        logger.error(
            f"Quarantined {len(quarantined)} / {len(records)} invalid records "
            f"for {source_name} due to Schema Drift!"
        )

    if not valid_records:
        raise ValueError(
            f"All records for {source_name} failed schema validation gate!"
        )

    return valid_records
