import os
from pathlib import Path

from flask import Flask

from .http import register_http_handlers
from .logging_config import configure_json_logging
from .observability import RequestMetrics
from .redis_client import create_redis_client
from .routes import register_routes

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_APP_VERSION = (PROJECT_ROOT / "VERSION").read_text().strip()


def create_app(redis_client=None) -> Flask:
    application = Flask(
        "app",
        static_folder=str(PROJECT_ROOT / "static"),
        template_folder=str(PROJECT_ROOT / "templates"),
    )
    application.config.from_mapping(
        APP_VERSION=os.getenv("APP_VERSION", DEFAULT_APP_VERSION),
        APP_ENVIRONMENT=os.getenv("APP_ENVIRONMENT", "development"),
    )
    configure_json_logging(application)

    client = redis_client if redis_client is not None else create_redis_client()
    request_metrics = RequestMetrics(client)
    register_http_handlers(application, request_metrics)
    register_routes(application, client, request_metrics)

    return application
