FROM python:3.13.14-slim@sha256:bf503bb2243c5aad0aa951544dd60d165f992646441d35dea90893703fc26251

ARG IMAGE_SOURCE="https://github.com/keregan/devops-notes-lab"
LABEL org.opencontainers.image.source="${IMAGE_SOURCE}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --disable-pip-version-check -r requirements.txt

COPY app.py gunicorn_config.py ./
COPY devops_notes_lab ./devops_notes_lab
COPY VERSION .
COPY static ./static
COPY templates ./templates

USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/ready', timeout=2)"]

CMD ["gunicorn", "--config", "gunicorn_config.py", "app:app"]
