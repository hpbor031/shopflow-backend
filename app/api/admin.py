"""
管理模块接口层（app/api/admin.py）

本文件里的所有接口都要求「管理员身份」，
统一通过 get_current_admin 依赖把关：

- 未登录 / token 非法 / 过期          → 401
- 已登录但不是管理员（role != 2）      → 403 需要管理员权限
- 已登录但账号被禁用（status = 0）     → 403 账号已被禁用

接口分组：
- 用户管理：GET /admin/users、PATCH /admin/users/{user_id}/status
- 商品管理：GET /admin/products（含已下架商品）
- 订单管理：GET /admin/orders、PATCH /admin/orders/{order_id}/status

商品的增删改、分类的增删改查已经有现成接口，管理端直接复用，这里不再重复实现。
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.database import get_session
from app.models.models import User
from app.schemas.order import OrderListItemResponse, OrderResponse, OrderStatusUpdate
from app.schemas.product import ProductOut
from app.schemas.user import UserMeResponse, UserStatusUpdate
from app.services.admin import (
    get_admin_orders_service,
    get_admin_products_service,
    get_users_service,
    update_user_status_service,
)
from app.services.order import admin_update_order_status_service

router = APIRouter()


# ==================== 用户管理 ====================

@router.get("/admin/users", response_model=list[UserMeResponse])
async def get_users_api(
    db: AsyncSession = Depends(get_session),
    _current_admin: User = Depends(get_current_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    """
    管理员查看用户列表（分页）。

参数说明：
db：数据库异步会话。
_current_admin：管理员门禁，非管理员进不来（下划线开头表示只用它做校验，不读它的字段）。
page：当前页码，从 1 开始。
page_size：每页条数，默认 10 条，最多 100 条。

功能说明：
分页返回用户信息（id、用户名、邮箱、状态、角色、注册时间）。
响应由 UserMeResponse 白名单控制，password_hash 永远不会被返回。
翻到没有数据的页返回空列表 []，不算错误；前端可用「返回条数 < page_size」判断是否最后一页。
    """
    return await get_users_service(db=db, page=page, page_size=page_size)


@router.patch("/admin/users/{user_id}/status", response_model=UserMeResponse)
async def update_user_status_api(
    user_id: int,
    data: UserStatusUpdate,
    db: AsyncSession = Depends(get_session),
    _current_admin: User = Depends(get_current_admin),
):
    """
    管理员启用 / 禁用用户。

参数说明：
user_id：要修改的用户 ID。
data：目标状态，1=正常（可登录）0=禁用。
db：数据库异步会话。

功能说明：
禁用用户后，该用户即使手里还有未过期的 token 也会被 get_current_user 拦下并返回 403，
所以禁用是立即生效的；重新把状态改成 1 即可恢复。
用户不存在返回 404。返回修改后的用户信息（不含密码哈希）。
    """
    return await update_user_status_service(user_id=user_id, data=data, db=db)


# ==================== 商品管理 ====================

@router.get("/admin/products", response_model=list[ProductOut])
async def get_admin_products_api(
    db: AsyncSession = Depends(get_session),
    _current_admin: User = Depends(get_current_admin),
    keyword: str | None = None,
    category_id: int | None = None,
    status: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    """
    管理员查看商品列表（含已下架商品，分页）。

参数说明：
db：数据库异步会话。
keyword：商品名称关键词，可选。
category_id：按分类筛选，可选。
status：按状态筛选（1=上架 0=下架），可选；不传时商品列表不限制状态。
page / page_size：分页参数，page_size 最多 100。

功能说明：
与前台 GET /products 的区别是「不传 status 时也能看到已下架商品」，
方便管理员查看全量数据、决定上下架。
排序固定按创建时间倒序（最近新增/上架的排在前面）。
商品的创建、修改、下架沿用 POST /products、PUT /products/{id}、DELETE /products/{id}。
    """
    return await get_admin_products_service(
        db=db,
        keyword=keyword,
        category_id=category_id,
        status=status,
        page=page,
        page_size=page_size,
    )


# ==================== 订单管理 ====================

@router.get("/admin/orders", response_model=list[OrderListItemResponse])
async def get_admin_orders_api(
    db: AsyncSession = Depends(get_session),
    _current_admin: User = Depends(get_current_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    """
    管理员查看全部用户的订单（分页，新订单在前）。

参数说明：
db：数据库异步会话。
page / page_size：分页参数，page_size 最多 100。

功能说明：
不做用户过滤，返回全平台订单的主表信息（订单号、下单用户、总金额、状态、时间），
不含商品明细；要看某条订单买了什么，调用 PATCH 改成相应状态或查 /orders/{order_id} 的
用户端接口（管理员查详情可直接用返回的订单 ID 配合管理端状态接口）。
    """
    return await get_admin_orders_service(db=db, page=page, page_size=page_size)


@router.patch("/admin/orders/{order_id}/status", response_model=OrderResponse)
async def update_order_status_admin_api(
    order_id: int,
    data: OrderStatusUpdate,
    db: AsyncSession = Depends(get_session),
    _current_admin: User = Depends(get_current_admin),
):
    """
    管理员修改任意用户的订单状态（发货、完成、取消等）。

参数说明：
order_id：要修改的订单 ID。
data：目标状态，1=待付款 2=已付款 3=已发货 4=已完成 5=已取消。
db：数据库异步会话。

功能说明：
与用户端的 PATCH /orders/{order_id}/status 共用同一套状态机与事务逻辑，
区别是不校验订单归属（管理员可以操作所有用户的订单）。
订单不存在返回 404；非法流转（如「已完成 → 待付款」）返回 400；
改成「已取消」时会把库存与销量归还商品表。
返回订单主表字段 + items 明细，结构与用户端一致。
    """
    return await admin_update_order_status_service(order_id=order_id, data=data, db=db)
