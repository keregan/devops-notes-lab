import socket
from http import HTTPStatus

from flask import Flask, Response, g, jsonify, render_template
from redis import Redis
from redis.exceptions import RedisError

from .http import error_response
from .observability import RequestMetrics
from .redis_client import VISITS_KEY


def register_routes(
    application: Flask,
    client: Redis,
    request_metrics: RequestMetrics,
) -> None:
    @application.get("/")
    def index():
        try:
            visits = int(client.incr(VISITS_KEY))
        except RedisError:
            application.logger.exception(
                "Redis is unavailable",
                extra={
                    "event": "dependency_error",
                    "request_id": g.request_id,
                    "dependency": "redis",
                },
            )
            return error_response(
                HTTPStatus.SERVICE_UNAVAILABLE,
                "Redis is unavailable",
                dependency="redis",
            )

        return render_template(
            "index.html",
            visits=visits,
            app_version=application.config["APP_VERSION"],
            app_environment=application.config["APP_ENVIRONMENT"],
        )

    @application.get("/health")
    def health():
        return jsonify(status="ok", service="devops-notes-lab")

    @application.get("/ready")
    def ready():
        try:
            client.ping()
        except RedisError:
            return error_response(
                HTTPStatus.SERVICE_UNAVAILABLE,
                "Service is not ready",
                dependencies={"redis": "unavailable"},
            )

        return jsonify(status="ready", dependencies={"redis": "ok"})

    @application.get("/info")
    def info():
        return jsonify(
            service="devops-notes-lab",
            version=application.config["APP_VERSION"],
            environment=application.config["APP_ENVIRONMENT"],
            hostname=socket.gethostname(),
        )

    @application.get("/metrics")
    def metrics():
        redis_up = 1
        try:
            stored_visits = client.get(VISITS_KEY)
        except RedisError:
            redis_up = 0
            visits = 0
        else:
            try:
                visits = int(stored_visits or 0)
            except (TypeError, ValueError):
                visits = 0
                application.logger.error(
                    "Redis visit counter is invalid",
                    extra={
                        "event": "dependency_data_error",
                        "request_id": g.request_id,
                        "dependency": "redis",
                    },
                )

        body = (
            "# HELP devops_notes_lab_up Whether the application is running.\n"
            "# TYPE devops_notes_lab_up gauge\n"
            "devops_notes_lab_up 1\n"
            "# HELP devops_notes_lab_redis_up Whether Redis is reachable.\n"
            "# TYPE devops_notes_lab_redis_up gauge\n"
            f"devops_notes_lab_redis_up {redis_up}\n"
            "# HELP devops_notes_lab_visits_total Total page visits stored in Redis.\n"
            "# TYPE devops_notes_lab_visits_total counter\n"
            f"devops_notes_lab_visits_total {visits}\n"
            f"{request_metrics.render()}"
        )
        return Response(
            body,
            content_type="text/plain; version=0.0.4; charset=utf-8",
        )
