"""
Redis 异步连接（app/core/redis_client.py）。

只负责创建连接、启动探测和关闭连接，暂不包含商品缓存业务。
"""

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import (
    REDIS_DB,
    REDIS_ENABLED,
    REDIS_HOST,
    REDIS_PASSWORD,
    REDIS_PORT,
    REDIS_SOCKET_TIMEOUT_SECONDS,
)
from app.core.logger import get_logger

logger = get_logger(__name__)

_redis_client: Redis | None = None


def get_redis_client() -> Redis | None:
    """返回进程中共享的异步 Redis 客户端。"""
    global _redis_client

    if not REDIS_ENABLED:
        return None

    if _redis_client is None:
        _redis_client = Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD,
            decode_responses=True,
            socket_connect_timeout=REDIS_SOCKET_TIMEOUT_SECONDS,
            socket_timeout=REDIS_SOCKET_TIMEOUT_SECONDS,
            health_check_interval=30,
        )

    return _redis_client


async def init_redis() -> bool:
    """
    应用启动时探测 Redis。

    连接失败返回 False，但不阻止应用启动。
    """
    client = get_redis_client()
    if client is None:
        logger.info("Redis 缓存已关闭")
        return False

    try:
        await client.ping()
        logger.info(
            "Redis 连接成功：%s:%s/%s",
            REDIS_HOST,
            REDIS_PORT,
            REDIS_DB,
        )
        return True
    except RedisError as exc:
        logger.warning("Redis 连接失败，后续将回落 MySQL：%s", exc)
        return False


async def close_redis() -> None:
    """应用关闭时释放 Redis 连接池。"""
    global _redis_client

    if _redis_client is None:
        return

    await _redis_client.aclose()
    _redis_client = None