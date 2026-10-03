"""
管理模块业务逻辑（app/services/admin.py）

管理模块只做「管理员视角」的查询与状态管理：

- 用户管理：查看用户列表、启用 / 禁用用户
- 商品管理：查看全部商品（含已下架）
- 订单管理：查看全部用户的订单

已经存在的接口直接复用，不重复实现：
- 商品的增删改查沿用 /products（接口内部走同一套 service / CRUD）
- 分类的增删改查沿用 /categories

权限判断不在这里做：是不是管理员由 API 层的 get_current_admin 依赖把关，
Service 层只负责业务规则（比如「用户不存在要报 404」），职责单一好维护。
"""

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.CRUD.order import get_orders
from app.CRUD.user import get_user_by_id, get_users, update_user_status
from app.schemas.user import UserStatusUpdate
from app.services.product import list_product_service


async def get_users_service(db:AsyncSession,page:int=1,page_size:int=10):
    """
    管理员查看用户列表（分页，先注册的排在前面）。

    返回的是 ORM 的 User 对象列表，
    响应字段由 UserMeResponse 白名单决定，password_hash 不会外泄。
    """
    return await get_users(db, page=page, page_size=page_size)


async def update_user_status_service(user_id:int,data:UserStatusUpdate,db:AsyncSession):
    """
    管理员启用 / 禁用用户。

    user_id：目标用户 ID，用户不存在返回 404。
    data.status：1=正常 0=禁用。
    禁用后该用户已签发的 token 也立即失效（get_current_user 会返回 403）。
    """
    user = await get_user_by_id(user_id, db)
    if user is None:
        raise HTTPException(
            status_code=404,
            detail="用户不存在"
        )
    return await update_user_status(user, data.status, db)


async def get_admin_products_service(
    db:AsyncSession,
    keyword:str | None = None,
    category_id:int | None = None,
    status:int | None = None,
    page:int = 1,
    page_size:int = 10
):
    """
    管理员查看商品列表（分页）。

    与前台 GET /products 的区别只有一点：only_online=False，
    不传 status 时能看到全部商品（包括已下架的），方便做上下架管理。
    排序固定为「按创建时间倒序」，管理端一般只关心最近改动的商品。
    """
    return await list_product_service(
        db,
        keyword=keyword,
        category_id=category_id,
        status=status,
        sort_by="created_at",
        order="desc",
        page=page,
        page_size=page_size,
        only_online=False,
    )


async def get_admin_orders_service(db:AsyncSession,page:int=1,page_size:int=10):
    """
    管理员查看全部用户的订单（分页，新订单在前，只返回订单主表）。

    user_id 传 None 表示不按用户过滤，复用用户端同一套分页查询逻辑。
    """
    return await get_orders(None, db, page=page, page_size=page_size)
