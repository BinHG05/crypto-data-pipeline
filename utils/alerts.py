import json
from typing import Any

import requests

from config.settings import ALERT_EMAIL_TO, SLACK_WEBHOOK_URL
from utils.logger import get_logger

logger = get_logger(__name__)


def _build_alert_message(context: dict[str, Any]) -> str:
    dag_run = context.get("dag_run")
    task_instance = context.get("task_instance")
    exception = context.get("exception")
    dag = context.get("dag")

    dag_id = getattr(dag_run, "dag_id", getattr(dag, "dag_id", "unknown"))
    run_id = getattr(dag_run, "run_id", "unknown")
    task_id = getattr(task_instance, "task_id", "unknown")
    log_url = getattr(task_instance, "log_url", "")

    return (
        f"Airflow alert\n"
        f"DAG: {dag_id}\n"
        f"Task: {task_id}\n"
        f"Run ID: {run_id}\n"
        f"Exception: {exception}\n"
        f"Log URL: {log_url}"
    )


def _send_email_alert(subject: str, body: str) -> None:
    if not ALERT_EMAIL_TO:
        logger.info("Email alert skipped because ALERT_EMAIL_TO is not configured")
        return

    try:
        from airflow.utils.email import send_email
    except Exception as exc:
        logger.error(f"Airflow email backend unavailable | error={exc}")
        return

    try:
        send_email(ALERT_EMAIL_TO, subject, body)
        logger.info(
            "Sent Airflow email alert successfully | "
            f"recipients={','.join(ALERT_EMAIL_TO)}"
        )
    except Exception as exc:
        logger.error(f"Failed to send Airflow email alert | error={exc}")


def _send_slack_alert(body: str) -> None:
    if not SLACK_WEBHOOK_URL:
        logger.info("Slack alert skipped because SLACK_WEBHOOK_URL is not configured")
        return

    try:
        response = requests.post(
            SLACK_WEBHOOK_URL,
            headers={"Content-Type": "application/json"},
            data=json.dumps({"text": body}),
            timeout=15,
        )
        response.raise_for_status()
        logger.info("Sent Slack alert successfully")
    except requests.RequestException as exc:
        logger.error(f"Failed to send Slack alert | error={exc}")


def send_failure_alert(context: dict[str, Any]) -> None:
    task_instance = context["task_instance"]
    message = _build_alert_message(context)
    subject = f"[Airflow] Failure in {task_instance.dag_id}.{task_instance.task_id}"

    logger.warning(
        "Dispatching failure alert | "
        f"dag={task_instance.dag_id} | task={task_instance.task_id}"
    )

    _send_email_alert(subject, message)
    _send_slack_alert(message)
