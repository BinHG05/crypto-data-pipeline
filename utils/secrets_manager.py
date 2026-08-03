"""
Secrets Manager Abstraction Layer for Data Pipeline
Supports:
1. Dynamic retrieval from GCP Secret Manager (if configured / available)
2. Dynamic retrieval from AWS Secrets Manager / Parameter Store (if configured / available)
3. Graceful fallback to local environment variables (.env) for local dev & zero-cost operation.
"""

import os
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)


def get_secret_from_gcp(
    secret_id: str, project_id: Optional[str] = None
) -> Optional[str]:
    """Retrieve secret from GCP Secret Manager."""
    try:
        from google.cloud import secretmanager

        client = secretmanager.SecretManagerServiceClient()
        proj = project_id or os.getenv("GCP_PROJECT_ID", "snappy-monolith-481115-e5")
        name = f"projects/{proj}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        secret_val = response.payload.data.decode("UTF-8").strip()
        logger.info(
            f"Successfully retrieved secret '{secret_id}' from GCP Secret Manager"
        )
        return secret_val
    except Exception as exc:
        logger.debug(
            f"Could not fetch secret '{secret_id}' from GCP Secret Manager: {exc}"
        )
        return None


def get_secret_from_aws(
    secret_name: str, region_name: Optional[str] = None
) -> Optional[str]:
    """Retrieve secret from AWS Secrets Manager."""
    try:
        import boto3

        region = region_name or os.getenv("AWS_DEFAULT_REGION", "ap-southeast-1")
        client = boto3.client("secretsmanager", region_name=region)
        response = client.get_secret_value(SecretId=secret_name)
        if "SecretString" in response:
            logger.info(
                f"Successfully retrieved secret '{secret_name}' from AWS Secrets Manager"
            )
            return response["SecretString"].strip()
    except Exception as exc:
        logger.debug(
            f"Could not fetch secret '{secret_name}' from AWS Secrets Manager: {exc}"
        )
        return None


def get_secret(
    name: str, default: str = "", provider_priority: str = "env_first"
) -> str:
    """
    Unified secret retriever.
    - provider_priority='env_first' (Default for zero-cost & local dev):
        Checks OS Environment (.env) first. If absent or empty, attempts Cloud Secret Managers.
    - provider_priority='cloud_first':
        Attempts Cloud Secret Managers first. Falls back to OS Environment (.env).
    """
    if provider_priority == "env_first":
        env_val = os.getenv(name)
        if env_val is not None and env_val.strip() != "":
            return env_val.strip()

    gcp_val = get_secret_from_gcp(name)
    if gcp_val:
        return gcp_val

    aws_val = get_secret_from_aws(name)
    if aws_val:
        return aws_val

    env_val = os.getenv(name, default)
    return env_val.strip() if env_val else default
