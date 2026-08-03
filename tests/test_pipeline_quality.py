"""
Unit Tests for Data Pipeline Quality Gates & Core Utilities
"""

import unittest
from utils.schema_validator import CoinGeckoRecord, FearGreedRecord, validate_records
from utils.secrets_manager import get_secret
from utils.alerts import _build_alert_message


class TestPipelineQuality(unittest.TestCase):

    def test_coingecko_schema_validator_valid(self):
        sample_data = [
            {
                "symbol": "bitcoin",
                "price": 65000.5,
                "timestamp": "2026-07-23 12:00:00",
                "ingestion_date": "2026-07-23",
            }
        ]
        validated = validate_records(sample_data, CoinGeckoRecord, "CoinGeckoTest")
        self.assertEqual(len(validated), 1)
        self.assertEqual(validated[0]["symbol"], "bitcoin")
        self.assertEqual(validated[0]["price"], 65000.5)

    def test_fear_greed_schema_validator_valid(self):
        sample_data = [
            {
                "value": 75,
                "value_classification": "Greed",
                "timestamp": 1721736000,
                "ingestion_date": "2026-07-23",
            }
        ]
        validated = validate_records(sample_data, FearGreedRecord, "FearGreedTest")
        self.assertEqual(len(validated), 1)
        self.assertEqual(validated[0]["value"], 75)

    def test_secrets_manager_fallback(self):
        val = get_secret("NON_EXISTENT_TEST_SECRET_KEY_12345", default="fallback_val")
        self.assertEqual(val, "fallback_val")

    def test_alert_message_builder(self):
        mock_context = {
            "dag_run": type(
                "DAGRun", (), {"dag_id": "crypto_pipeline_v2", "run_id": "manual__test"}
            )(),
            "task_instance": type(
                "TaskInstance",
                (),
                {"task_id": "fetch_coingecko", "log_url": "http://localhost/log"},
            )(),
            "exception": "API Timeout Exception",
        }
        msg = _build_alert_message(mock_context)
        self.assertIn("crypto_pipeline_v2", msg)
        self.assertIn("fetch_coingecko", msg)
        self.assertIn("API Timeout Exception", msg)


if __name__ == "__main__":
    unittest.main()
