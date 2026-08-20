import json
import logging
import os
import unittest
from io import StringIO
from unittest.mock import patch
from uuid import UUID

from redis.exceptions import RedisError

from app import JsonFormatter, create_app


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


class FalseyRedis(FakeRedis):
    def __bool__(self):
        return False


class InvalidCounterRedis(FakeRedis):
    def get(self, _key):
        return "not-a-number"


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

    def test_falsey_injected_redis_client_is_preserved(self):
        redis = FalseyRedis()
        application = create_app(redis)
        application.config.update(TESTING=True)

        response = application.test_client().get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(redis.visits, 1)

    def test_health_reports_running_application(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_response_contains_generated_request_id(self):
        response = self.client.get("/health")

        request_id = response.headers["X-Request-ID"]
        self.assertEqual(str(UUID(request_id)), request_id)

    def test_response_preserves_client_request_id(self):
        request_id = "manual-check-123"

        response = self.client.get(
            "/info",
            headers={"X-Request-ID": request_id},
        )

        self.assertEqual(response.headers["X-Request-ID"], request_id)

    def test_invalid_client_request_id_is_replaced(self):
        for request_id in ("contains spaces", "contains/slash", "кириллица"):
            with self.subTest(request_id=request_id):
                response = self.client.get(
                    "/info",
                    headers={"X-Request-ID": request_id},
                )

                generated_id = response.headers["X-Request-ID"]
                self.assertNotEqual(generated_id, request_id)
                self.assertEqual(str(UUID(generated_id)), generated_id)

    def test_oversized_client_request_id_is_replaced(self):
        request_id = "x" * 129

        response = self.client.get(
            "/info",
            headers={"X-Request-ID": request_id},
        )

        generated_id = response.headers["X-Request-ID"]
        self.assertNotEqual(generated_id, request_id)
        self.assertEqual(str(UUID(generated_id)), generated_id)

    def test_request_log_uses_structured_json(self):
        output = StringIO()
        handler = logging.StreamHandler(output)
        handler.setFormatter(JsonFormatter())
        self.client.application.logger.addHandler(handler)

        try:
            response = self.client.get("/health")
        finally:
            self.client.application.logger.removeHandler(handler)

        log_entry = json.loads(output.getvalue().strip())

        self.assertEqual(log_entry["event"], "http_request_completed")
        self.assertEqual(log_entry["level"], "INFO")
        self.assertEqual(log_entry["method"], "GET")
        self.assertEqual(log_entry["path"], "/health")
        self.assertEqual(log_entry["status_code"], 200)
        self.assertEqual(log_entry["request_id"], response.headers["X-Request-ID"])
        self.assertGreaterEqual(log_entry["duration_ms"], 0)

    def test_response_contains_security_headers(self):
        response = self.client.get("/")

        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")
        self.assertEqual(response.headers["Referrer-Policy"], "no-referrer")
        self.assertIn(
            "default-src 'self'",
            response.headers["Content-Security-Policy"],
        )
        self.assertIn(
            "style-src 'self'",
            response.headers["Content-Security-Policy"],
        )
        self.assertNotIn(
            "'unsafe-inline'",
            response.headers["Content-Security-Policy"],
        )

    def test_home_page_loads_external_stylesheet(self):
        response = self.client.get("/")

        self.assertIn(b'href="/static/styles.css"', response.data)
        self.assertNotIn(b"<style", response.data)

    def test_static_stylesheet_is_available(self):
        with self.client.get("/static/styles.css") as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.mimetype, "text/css")
            self.assertIn(b"color-scheme: dark", response.data)

    def test_security_headers_are_added_to_error_responses(self):
        response = self.client.get("/does-not-exist")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")

    def test_health_stays_available_when_redis_is_down(self):
        application = create_app(FakeRedis(available=False))
        application.config.update(TESTING=True)

        response = application.test_client().get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_home_page_returns_503_when_redis_is_unavailable(self):
        redis = FakeRedis(available=False)
        application = create_app(redis)
        application.config.update(TESTING=True)

        with self.assertLogs(application.logger, level="ERROR") as logs:
            response = application.test_client().get("/")
        payload = response.get_json()

        self.assertEqual(response.status_code, 503)
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["code"], 503)
        self.assertEqual(payload["message"], "Redis is unavailable")
        self.assertEqual(payload["dependency"], "redis")
        self.assertEqual(payload["request_id"], response.headers["X-Request-ID"])
        self.assertEqual(redis.visits, 0)
        self.assertIn("Redis is unavailable", logs.output[0])

    def test_ready_checks_redis(self):
        response = self.client.get("/ready")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["dependencies"]["redis"], "ok")

    def test_ready_returns_503_when_redis_is_unavailable(self):
        application = create_app(FakeRedis(available=False))
        application.config.update(TESTING=True)

        response = application.test_client().get("/ready")
        payload = response.get_json()

        self.assertEqual(response.status_code, 503)
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["code"], 503)
        self.assertEqual(payload["message"], "Service is not ready")
        self.assertEqual(payload["dependencies"]["redis"], "unavailable")
        self.assertEqual(payload["request_id"], response.headers["X-Request-ID"])

    def test_info_reports_deployment_metadata(self):
        environment = {
            "APP_VERSION": "1.3.0-test",
            "APP_ENVIRONMENT": "test",
        }
        with patch.dict(os.environ, environment):
            application = create_app(self.redis)
            application.config.update(TESTING=True)

        response = application.test_client().get("/info")
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["service"], "devops-notes-lab")
        self.assertEqual(payload["version"], "1.3.0-test")
        self.assertEqual(payload["environment"], "test")
        self.assertTrue(payload["hostname"])

    def test_info_uses_safe_default_metadata(self):
        with patch.dict(os.environ, {}, clear=True):
            application = create_app(self.redis)
            application.config.update(TESTING=True)

        response = application.test_client().get("/info")
        payload = response.get_json()

        self.assertEqual(payload["version"], "1.3.0")
        self.assertEqual(payload["environment"], "development")

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

    def test_metrics_start_at_zero_and_follow_prometheus_format(self):
        response = self.client.get("/metrics")
        metrics = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/plain")
        self.assertIn("version=0.0.4", response.content_type)
        self.assertIn("# TYPE devops_notes_lab_up gauge", metrics)
        self.assertIn("# TYPE devops_notes_lab_visits_total counter", metrics)
        self.assertIn("devops_notes_lab_visits_total 0", metrics)
        self.assertEqual(self.redis.visits, 0)

    def test_metrics_report_redis_outage_without_failing_scrape(self):
        application = create_app(FakeRedis(available=False))
        application.config.update(TESTING=True)

        response = application.test_client().get("/metrics")

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "devops_notes_lab_redis_up 0",
            response.get_data(as_text=True),
        )

    def test_metrics_handle_invalid_redis_counter_without_failing_scrape(self):
        application = create_app(InvalidCounterRedis())
        application.config.update(TESTING=True)

        with self.assertLogs(application.logger, level="ERROR") as logs:
            response = application.test_client().get("/metrics")
        metrics = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("devops_notes_lab_redis_up 1", metrics)
        self.assertIn("devops_notes_lab_visits_total 0", metrics)
        self.assertIn("Redis visit counter is invalid", logs.output[0])

    def test_unknown_route_returns_json_error(self):
        response = self.client.get("/does-not-exist")
        payload = response.get_json()

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.mimetype, "application/json")
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["code"], 404)
        self.assertEqual(payload["message"], "Resource not found")
        self.assertEqual(payload["request_id"], response.headers["X-Request-ID"])

    def test_unhandled_exception_returns_safe_json_error(self):
        application = create_app(self.redis)
        application.config.update(TESTING=False, PROPAGATE_EXCEPTIONS=False)

        @application.get("/test-error")
        def trigger_error():
            raise RuntimeError("private exception details")

        with self.assertLogs(application.logger, level="ERROR"):
            response = application.test_client().get("/test-error")
        payload = response.get_json()

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.mimetype, "application/json")
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["code"], 500)
        self.assertEqual(payload["message"], "Internal server error")
        self.assertEqual(payload["request_id"], response.headers["X-Request-ID"])
        self.assertNotIn("private exception details", response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
