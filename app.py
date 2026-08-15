import os
import socket
from http import HTTPStatus
from uuid import uuid4

from flask import Flask, Response, g, jsonify, render_template, request
from redis import Redis
from redis.exceptions import RedisError

VISITS_KEY = "devops-notes-lab:visits"


def create_redis_client() -> Redis:
    return Redis(
        host=os.getenv("REDIS_HOST", "redis"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=int(os.getenv("REDIS_DB", "0")),
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=1,
        health_check_interval=30,
    )


def create_app(redis_client=None) -> Flask:
    application = Flask(__name__)
    application.config.from_mapping(
        APP_VERSION=os.getenv("APP_VERSION", "1.2.2"),
        APP_ENVIRONMENT=os.getenv("APP_ENVIRONMENT", "development"),
    )
    client = redis_client or create_redis_client()

    @application.before_request
    def assign_request_id():
        g.request_id = request.headers.get("X-Request-ID") or str(uuid4())

    @application.after_request
    def add_request_id(response):
        response.headers["X-Request-ID"] = g.request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "frame-ancestors 'none'; "
            "base-uri 'none'"
        )
        return response

    @application.errorhandler(HTTPStatus.NOT_FOUND)
    @application.errorhandler(HTTPStatus.INTERNAL_SERVER_ERROR)
    def json_error_response(error):
        code = int(error.code or HTTPStatus.INTERNAL_SERVER_ERROR)
        message = (
            "Resource not found"
            if code == HTTPStatus.NOT_FOUND
            else "Internal server error"
        )
        return (
            jsonify(
                status="error",
                code=code,
                message=message,
                request_id=g.request_id,
            ),
            code,
        )

    @application.get("/")
    def index():
        try:
            visits = int(client.incr(VISITS_KEY))
        except RedisError:
            application.logger.exception(
                "Redis is unavailable request_id=%s",
                g.request_id,
            )
            return (
                jsonify(status="error", message="Redis is unavailable"),
                HTTPStatus.SERVICE_UNAVAILABLE,
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
            return (
                jsonify(status="not_ready", dependencies={"redis": "unavailable"}),
                HTTPStatus.SERVICE_UNAVAILABLE,
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
            visits = int(client.get(VISITS_KEY) or 0)
        except RedisError:
            redis_up = 0
            visits = 0

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
        )
        return Response(
            body,
            content_type="text/plain; version=0.0.4; charset=utf-8",
        )

    return application


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
