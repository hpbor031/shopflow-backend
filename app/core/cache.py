"""Redis 缓存工具：JSON 读写与商品缓存版本管理。"""

import json
from typing import Any

from redis.exceptions import RedisError

from app.core.config import REDIS_CACHE_TTL_SECONDS
from app.core.logger import get_logger
from app.core.redis_client import get_redis_client

logger = get_logger(__name__)

PRODUCT_CACHE_PREFIX = "shopflow:products"
PRODUCT_CACHE_VERSION_KEY = f"{PRODUCT_CACHE_PREFIX}:cache-version"


async def cache_get_json(key: str) -> Any | None:
    """读取 JSON 缓存；未命中或 Redis 异常时返回 None。"""
    client = get_redis_client()
    if client is None:
        return None

    try:
        raw_value = await client.get(key)
    except RedisError as exc:
        logger.warning("Redis 读取失败，回落 MySQL：%s", exc)
        return None

    if raw_value is None:
        return None

    try:
        return json.loads(raw_value)
    except (TypeError, json.JSONDecodeError):
        logger.warning("缓存内容不是有效 JSON，已删除：%s", key)
        await cache_delete(key)
        return None


async def cache_set_json(
    key: str,
    value: Any,
    ttl_seconds: int | None = None,
) -> bool:
    """将数据序列化为 JSON 写入 Redis。"""
    client = get_redis_client()
    if client is None:
        return False

    try:
        payload = json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        await client.set(
            key,
            payload,
            ex=ttl_seconds or REDIS_CACHE_TTL_SECONDS,
        )
        return True
    except (RedisError, TypeError, ValueError) as exc:
        logger.warning("Redis 写入失败，不影响主流程：%s", exc)
        return False


async def cache_delete(key: str) -> None:
    """删除一个缓存键。"""
    client = get_redis_client()
    if client is None:
        return

    try:
        await client.delete(key)
    except RedisError as exc:
        logger.warning("Redis 删除失败：%s", exc)


async def get_product_cache_version() -> str | None:
    """
    获取商品缓存版本。

    版本号会写进所有商品缓存键。商品发生变化时递增版本号，
    旧缓存立即逻辑失效，不需要扫描 Redis。
    """
    client = get_redis_client()
    if client is None:
        return None

    try:
        version = await client.get(PRODUCT_CACHE_VERSION_KEY)

        if version is None:
            await client.set(PRODUCT_CACHE_VERSION_KEY, "1", nx=True)
            version = await client.get(PRODUCT_CACHE_VERSION_KEY)

        return version or "1"
    except RedisError as exc:
        logger.warning("读取商品缓存版本失败：%s", exc)
        return None


async def invalidate_product_cache() -> None:
    """商品、库存或销量变化后递增版本，使旧商品缓存失效。"""
    client = get_redis_client()
    if client is None:
        return

    try:
        await client.incr(PRODUCT_CACHE_VERSION_KEY)
    except RedisError as exc:
        logger.warning("商品缓存失效失败：%s", exc)