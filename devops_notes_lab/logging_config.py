import json
import logging
from datetime import UTC, datetime

from flask import Flask

LOG_FIELDS = (
    "event",
    "request_id",
    "method",
    "path",
    "status_code",
    "duration_ms",
    "dependency",
)


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": datetime.fromtimestamp(
                record.created,
                tz=UTC,
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in LOG_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def configure_json_logging(application: Flask) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    application.logger.handlers = [handler]
    application.logger.setLevel(logging.INFO)
    application.logger.propagate = False
