import json

from redis.exceptions import RedisError

HTTP_REQUESTS_KEY = "devops-notes-lab:metrics:http-requests"
HTTP_ERRORS_KEY = "devops-notes-lab:metrics:http-errors"
HTTP_DURATION_COUNT_KEY = "devops-notes-lab:metrics:http-duration-count"
HTTP_DURATION_SUM_KEY = "devops-notes-lab:metrics:http-duration-sum"


def _encode_labels(*values: str) -> str:
    return json.dumps(values, separators=(",", ":"))


def _decode_labels(value: str | bytes) -> tuple[str, ...]:
    if isinstance(value, bytes):
        value = value.decode()
    return tuple(json.loads(value))


def _escape_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def _labels(**values: str) -> str:
    rendered = ",".join(
        f'{name}="{_escape_label(value)}"' for name, value in values.items()
    )
    return f"{{{rendered}}}"


def _format_number(value: str | int | float) -> str:
    return f"{float(value):.9g}"


class RequestMetrics:
    def __init__(self, redis_client):
        self.redis_client = redis_client

    def observe(
        self,
        *,
        method: str,
        endpoint: str,
        status_code: int,
        duration_seconds: float,
    ) -> bool:
        request_labels = _encode_labels(method, endpoint, str(status_code))
        duration_labels = _encode_labels(method, endpoint)

        try:
            pipeline = self.redis_client.pipeline(transaction=False)
            pipeline.hincrby(HTTP_REQUESTS_KEY, request_labels, 1)
            pipeline.hincrby(HTTP_DURATION_COUNT_KEY, duration_labels, 1)
            pipeline.hincrbyfloat(
                HTTP_DURATION_SUM_KEY,
                duration_labels,
                duration_seconds,
            )
            if status_code >= 400:
                pipeline.hincrby(HTTP_ERRORS_KEY, request_labels, 1)
            pipeline.execute()
        except RedisError:
            return False

        return True

    def render(self) -> str:
        try:
            requests = self.redis_client.hgetall(HTTP_REQUESTS_KEY)
            errors = self.redis_client.hgetall(HTTP_ERRORS_KEY)
            duration_counts = self.redis_client.hgetall(HTTP_DURATION_COUNT_KEY)
            duration_sums = self.redis_client.hgetall(HTTP_DURATION_SUM_KEY)
        except RedisError:
            requests = {}
            errors = {}
            duration_counts = {}
            duration_sums = {}

        lines = [
            "# HELP devops_notes_lab_http_requests_total Total HTTP requests.",
            "# TYPE devops_notes_lab_http_requests_total counter",
        ]
        for encoded_labels, value in sorted(requests.items()):
            method, endpoint, status = _decode_labels(encoded_labels)
            lines.append(
                "devops_notes_lab_http_requests_total"
                f"{_labels(method=method, endpoint=endpoint, status=status)} "
                f"{_format_number(value)}"
            )

        lines.extend(
            (
                "# HELP devops_notes_lab_http_errors_total Total HTTP error responses.",
                "# TYPE devops_notes_lab_http_errors_total counter",
            )
        )
        for encoded_labels, value in sorted(errors.items()):
            method, endpoint, status = _decode_labels(encoded_labels)
            lines.append(
                "devops_notes_lab_http_errors_total"
                f"{_labels(method=method, endpoint=endpoint, status=status)} "
                f"{_format_number(value)}"
            )

        lines.extend(
            (
                "# HELP devops_notes_lab_http_request_duration_seconds "
                "HTTP request duration.",
                "# TYPE devops_notes_lab_http_request_duration_seconds summary",
            )
        )
        for encoded_labels, value in sorted(duration_counts.items()):
            method, endpoint = _decode_labels(encoded_labels)
            labels = _labels(method=method, endpoint=endpoint)
            lines.append(
                "devops_notes_lab_http_request_duration_seconds_count"
                f"{labels} {_format_number(value)}"
            )
            lines.append(
                "devops_notes_lab_http_request_duration_seconds_sum"
                f"{labels} {_format_number(duration_sums.get(encoded_labels, 0))}"
            )

        return "\n".join(lines) + "\n"
