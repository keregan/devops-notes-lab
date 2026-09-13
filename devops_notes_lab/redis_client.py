import os

from redis import Redis

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
