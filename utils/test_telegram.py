"""
Quick Test Script for Telegram Alerting
Usage:
    docker compose exec airflow-scheduler python /opt/airflow/utils/test_telegram.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from utils.alerts import send_failure_alert
from utils.logger import get_logger

logger = get_logger(__name__)


def test_telegram():
    print("--------------------------------------------------")
    print("🤖 TESTING TELEGRAM ALERT SYSTEM")
    print(
        f"Token Configured : {'YES' if TELEGRAM_BOT_TOKEN else 'NO (Value: ' + str(TELEGRAM_BOT_TOKEN) + ')'}"
    )
    print(
        f"Chat ID Configured: {'YES' if TELEGRAM_CHAT_ID else 'NO (Value: ' + str(TELEGRAM_CHAT_ID) + ')'}"
    )
    print("--------------------------------------------------")

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(
            "❌ ERROR: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing in your .env file!"
        )
        print("Please add them to your .env file:")
        print("  TELEGRAM_BOT_TOKEN=your_bot_token_here")
        print("  TELEGRAM_CHAT_ID=your_chat_id_here")
        sys.exit(1)

    # Simulated Airflow Context
    mock_context = {
        "dag_run": type(
            "DAGRun",
            (),
            {"dag_id": "test_crypto_pipeline", "run_id": "manual__test_run"},
        )(),
        "task_instance": type(
            "TaskInstance",
            (),
            {
                "task_id": "test_alert_task",
                "log_url": "http://localhost:8080/log?dag_id=test",
            },
        )(),
        "exception": "Simulated Test Exception: Failed to connect to CoinGecko API (Test Mode)",
    }

    print("🚀 Sending simulated Airflow failure alert to Telegram...")
    try:
        send_failure_alert(mock_context)
        print("✅ SUCCESS! Check your Telegram app for the alert message!")
    except Exception as exc:
        print(f"❌ FAILED to send alert: {exc}")


if __name__ == "__main__":
    test_telegram()
