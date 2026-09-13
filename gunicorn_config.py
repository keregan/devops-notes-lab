import os
from collections.abc import Mapping

SETTING_SPECS = {
    "workers": ("GUNICORN_WORKERS", 2, 1, 32),
    "threads": ("GUNICORN_THREADS", 4, 1, 64),
    "timeout": ("GUNICORN_TIMEOUT", 30, 1, 300),
    "graceful_timeout": ("GUNICORN_GRACEFUL_TIMEOUT", 30, 1, 300),
}


def load_settings(environment: Mapping[str, str] | None = None) -> dict[str, int]:
    environment = os.environ if environment is None else environment
    settings = {}

    for setting, (variable, default, minimum, maximum) in SETTING_SPECS.items():
        raw_value = environment.get(variable, str(default))
        try:
            value = int(raw_value)
        except ValueError as error:
            raise ValueError(
                f"{variable} must be an integer from {minimum} to {maximum}"
            ) from error

        if not minimum <= value <= maximum:
            raise ValueError(
                f"{variable} must be an integer from {minimum} to {maximum}"
            )
        settings[setting] = value

    return settings


_settings = load_settings()

bind = "0.0.0.0:8000"
workers = _settings["workers"]
threads = _settings["threads"]
timeout = _settings["timeout"]
graceful_timeout = _settings["graceful_timeout"]
accesslog = "-"
errorlog = "-"
worker_tmp_dir = "/tmp"
