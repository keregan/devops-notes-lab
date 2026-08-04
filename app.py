import os
from http import HTTPStatus

from flask import Flask, jsonify, render_template
from redis import Redis
from redis.exceptions import RedisError


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
    client = redis_client or create_redis_client()

    @application.get("/")
    def index():
        try:
            visits = int(client.incr("devops-notes-lab:visits"))
        except RedisError:
            application.logger.exception("Redis is unavailable")
            return (
                jsonify(status="error", message="Redis is unavailable"),
                HTTPStatus.SERVICE_UNAVAILABLE,
            )

        return render_template("index.html", visits=visits)

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

    return application


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
