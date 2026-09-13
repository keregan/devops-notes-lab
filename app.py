from devops_notes_lab import create_app
from devops_notes_lab.logging_config import JsonFormatter

__all__ = ["JsonFormatter", "app", "create_app"]

app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
