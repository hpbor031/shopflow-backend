"""商品业务逻辑：协调 API、CRUD 与 Redis 缓存。"""

import hashlib
import json

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.CRUD.product import (
    product_create,
    product_delete,
    product_get,
    product_list,
    product_update,
)
from app.core.cache import (
    PRODUCT_CACHE_PREFIX,
    cache_get_json,
    cache_set_json,
    get_product_cache_version,
    invalidate_product_cache,
)
from app.schemas.product import ProductCreate, ProductOut, ProductUpdate


def _product_payload(product) -> dict:
    """把 ORM 商品转换为可写入 Redis 的 JSON 数据。"""
    return ProductOut.model_validate(product).model_dump(mode="json")


def _detail_cache_key(version: str, product_id: int) -> str:
    """生成带缓存版本的商品详情键。"""
    return f"{PRODUCT_CACHE_PREFIX}:{version}:detail:{product_id}"


def _list_cache_key(
    version: str,
    *,
    keyword: str | None,
    category_id: int | None,
    status: int | None,
    sort_by: str,
    order: str,
    page: int,
    page_size: int,
    only_online: bool,
) -> str:
    """把全部查询参数编码成稳定的商品列表缓存键。"""
    query = [
        keyword.strip() if keyword else None,
        category_id,
        status,
        sort_by,
        order,
        page,
        page_size,
        only_online,
    ]
    raw_query = json.dumps(
        query,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    query_hash = hashlib.sha256(raw_query.encode("utf-8")).hexdigest()
    return f"{PRODUCT_CACHE_PREFIX}:{version}:list:{query_hash}"


async def get_product_service(product_id: int, db: AsyncSession):
    """优先读取商品详情缓存，未命中时查询 MySQL 并写回 Redis。"""
    version = await get_product_cache_version()
    cache_key = _detail_cache_key(version, product_id) if version else None

    if cache_key:
        cached = await cache_get_json(cache_key)
        if isinstance(cached, dict):
            return cached

    product_obj = await product_get(product_id, db)
    if product_obj is None:
        raise HTTPException(status_code=404, detail="商品不存在")

    payload = _product_payload(product_obj)

    if cache_key:
        await cache_set_json(cache_key, payload)

    return payload


async def list_product_service(
    db: AsyncSession,
    keyword: str | None = None,
    category_id: int | None = None,
    status: int | None = None,
    sort_by: str = "created_at",
    order: str = "desc",
    page: int = 1,
    page_size: int = 10,
    only_online: bool = True,
):
    """优先读取商品列表缓存，未命中时查询 MySQL 并写回 Redis。"""
    version = await get_product_cache_version()
    cache_key = (
        _list_cache_key(
            version,
            keyword=keyword,
            category_id=category_id,
            status=status,
            sort_by=sort_by,
            order=order,
            page=page,
            page_size=page_size,
            only_online=only_online,
        )
        if version
        else None
    )

    if cache_key:
        cached = await cache_get_json(cache_key)
        if isinstance(cached, list):
            return cached

    products = await product_list(
        db,
        keyword=keyword,
        category_id=category_id,
        status=status,
        sort_by=sort_by,
        order=order,
        page=page,
        page_size=page_size,
        only_online=only_online,
    )

    if products is None:
        raise HTTPException(status_code=400, detail="排序参数错误")

    payload = [_product_payload(product) for product in products]

    if cache_key:
        await cache_set_json(cache_key, payload)

    return payload


async def create_product_service(product: ProductCreate, db: AsyncSession):
    """创建商品后递增缓存版本，使旧列表和详情缓存失效。"""
    product_obj = await product_create(product, db)
    await invalidate_product_cache()
    return product_obj


async def update_product_service(
    product_id: int,
    product: ProductUpdate,
    db: AsyncSession,
):
    """修改商品后让缓存失效。"""
    product_obj = await product_update(product_id, product, db)
    if product_obj is None:
        raise HTTPException(status_code=404, detail="商品不存在")

    await invalidate_product_cache()
    return product_obj


async def delete_product_service(product_id: int, db: AsyncSession):
    """下架商品后让缓存失效。"""
    product_obj = await product_delete(product_id, db)
    if product_obj is None:
        raise HTTPException(status_code=404, detail="商品不存在")

    await invalidate_product_cache()
    return product_obj
