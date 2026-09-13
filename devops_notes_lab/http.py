import re
import time
from http import HTTPStatus
from uuid import uuid4

from flask import Flask, g, jsonify, request

from .observability import RequestMetrics

REQUEST_ID_PATTERN = re.compile(r"[A-Za-z0-9._-]{1,128}")
QUIET_REQUEST_PATHS = frozenset({"/health", "/ready", "/metrics"})


def resolve_request_id(value: str | None) -> str:
    if value and REQUEST_ID_PATTERN.fullmatch(value):
        return value
    return str(uuid4())


def error_response(code: HTTPStatus, message: str, **details):
    payload = {
        "status": "error",
        "code": int(code),
        "message": message,
        "request_id": g.request_id,
        **details,
    }
    return jsonify(payload), code


def register_http_handlers(
    application: Flask,
    request_metrics: RequestMetrics,
) -> None:
    @application.before_request
    def assign_request_id():
        g.request_id = resolve_request_id(request.headers.get("X-Request-ID"))
        g.request_started_at = time.perf_counter()

    @application.after_request
    def add_request_id(response):
        duration_seconds = time.perf_counter() - g.request_started_at
        endpoint = request.url_rule.rule if request.url_rule else "unmatched"
        request_metrics.observe(
            method=request.method,
            endpoint=endpoint,
            status_code=response.status_code,
            duration_seconds=duration_seconds,
        )
        response.headers["X-Request-ID"] = g.request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "style-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'none'"
        )
        if response.status_code >= HTTPStatus.BAD_REQUEST or (
            request.path not in QUIET_REQUEST_PATHS
        ):
            application.logger.info(
                "HTTP request completed",
                extra={
                    "event": "http_request_completed",
                    "request_id": g.request_id,
                    "method": request.method,
                    "path": request.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_seconds * 1000, 3),
                },
            )
        return response

    @application.errorhandler(HTTPStatus.NOT_FOUND)
    @application.errorhandler(HTTPStatus.INTERNAL_SERVER_ERROR)
    def json_error_response(error):
        code = HTTPStatus(error.code or HTTPStatus.INTERNAL_SERVER_ERROR)
        message = (
            "Resource not found"
            if code == HTTPStatus.NOT_FOUND
            else "Internal server error"
        )
        return error_response(code, message)
