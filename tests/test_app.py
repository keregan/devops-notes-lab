import os
import unittest
from unittest.mock import patch

from redis.exceptions import RedisError

from app import create_app


class FakeRedis:
    def __init__(self, available=True):
        self.available = available
        self.visits = 0

    def incr(self, _key):
        if not self.available:
            raise RedisError("Redis is unavailable")
        self.visits += 1
        return self.visits

    def ping(self):
        if not self.available:
            raise RedisError("Redis is unavailable")
        return True

    def get(self, _key):
        if not self.available:
            raise RedisError("Redis is unavailable")
        return self.visits or None


class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.redis = FakeRedis()
        application = create_app(self.redis)
        application.config.update(TESTING=True)
        self.client = application.test_client()

    def test_home_page_uses_redis_counter(self):
        first_response = self.client.get("/")
        second_response = self.client.get("/")

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        self.assertIn(b"redis-connected", second_response.data)
        self.assertEqual(self.redis.visits, 2)

    def test_health_reports_running_application(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_ready_checks_redis(self):
        response = self.client.get("/ready")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["dependencies"]["redis"], "ok")

    def test_ready_returns_503_when_redis_is_unavailable(self):
        application = create_app(FakeRedis(available=False))
        application.config.update(TESTING=True)

        response = application.test_client().get("/ready")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()["status"], "not_ready")

    def test_info_reports_deployment_metadata(self):
        environment = {
            "APP_VERSION": "1.2.0-test",
            "APP_ENVIRONMENT": "test",
        }
        with patch.dict(os.environ, environment):
            application = create_app(self.redis)
            application.config.update(TESTING=True)

        response = application.test_client().get("/info")
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["service"], "devops-notes-lab")
        self.assertEqual(payload["version"], "1.2.0-test")
        self.assertEqual(payload["environment"], "test")
        self.assertTrue(payload["hostname"])

    def test_metrics_report_redis_and_visit_counter(self):
        self.client.get("/")
        self.client.get("/")

        response = self.client.get("/metrics")
        metrics = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content_type.startswith("text/plain"))
        self.assertIn("devops_notes_lab_up 1", metrics)
        self.assertIn("devops_notes_lab_redis_up 1", metrics)
        self.assertIn("devops_notes_lab_visits_total 2", metrics)
        self.assertEqual(self.redis.visits, 2)

    def test_metrics_report_redis_outage_without_failing_scrape(self):
        application = create_app(FakeRedis(available=False))
        application.config.update(TESTING=True)

        response = application.test_client().get("/metrics")

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "devops_notes_lab_redis_up 0",
            response.get_data(as_text=True),
        )


if __name__ == "__main__":
    unittest.main()
