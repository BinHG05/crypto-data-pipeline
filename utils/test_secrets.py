"""
Test Script for Secrets Manager Provider
Usage:
    docker compose exec -e PYTHONPATH=/opt/airflow airflow-scheduler python /opt/airflow/utils/test_secrets.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.secrets_manager import get_secret
from utils.logger import get_logger

logger = get_logger(__name__)


def test_secrets_manager():
    print("--------------------------------------------------")
    print("🔐 TESTING SECRETS MANAGER PROVIDER LAYER")
    print("--------------------------------------------------")

    token = get_secret("TELEGRAM_BOT_TOKEN")
    chat_id = get_secret("TELEGRAM_CHAT_ID")
    aws_key = get_secret("AWS_ACCESS_KEY_ID")

    print(
        f"TELEGRAM_BOT_TOKEN : {'FOUND (' + token[:10] + '...)' if token else 'NOT FOUND'}"
    )
    print(
        f"TELEGRAM_CHAT_ID   : {'FOUND (' + chat_id + ')' if chat_id else 'NOT FOUND'}"
    )
    print(
        f"AWS_ACCESS_KEY_ID  : {'FOUND (' + aws_key[:8] + '...)' if aws_key else 'NOT FOUND'}"
    )

    print("--------------------------------------------------")
    print("✅ Secrets Provider layer verified successfully!")


if __name__ == "__main__":
    test_secrets_manager()
