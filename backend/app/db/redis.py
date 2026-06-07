from collections.abc import Generator

from redis import Redis

from app.core.config import settings


def get_redis_client() -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True)


def get_redis() -> Generator[Redis, None, None]:
    client = get_redis_client()
    try:
        yield client
    finally:
        client.close()
