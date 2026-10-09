from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_session
from app.models.models import User
from app.schemas.order import OrderListItemResponse, OrderResponse, OrderStatusUpdate
from app.services.order import create_order_service, get_order_service, get_orders_service, update_order_status_service

router = APIRouter()

@router.post("/orders",response_model=OrderResponse)
async def create_order_api(
    db:AsyncSession = Depends(get_session),
    user:User = Depends(get_current_user)
):
    """
    创建订单（下单）：把当前登录用户的购物车结算成一张订单。

参数说明：
db：数据库异步会话，未登录或 Token 非法时请求进不来。
user：通过 Token 解析出的当前登录用户，下单人由 Token 决定，
请求体里没有 user_id，杜绝替别人下单。

功能说明：
获取当前登录用户的 ID，调用 Service 层的 create_order_service() 完成下单：
1. 购物车为空 → 400「购物车为空，无法创建订单」；
2. 商品已下架、库存不足 → 400，并带上具体商品名；
3. 校验通过则写入订单主表与订单明细，扣减库存、累加销量，最后清空购物车；
4. 返回新建订单（订单主表字段 + 全部订单明细）。
"""
    return await create_order_service(user_id=user.id,db=db)

@router.get("/orders",response_model=list[OrderListItemResponse])
async def get_orders_api(
    db:AsyncSession = Depends(get_session),
    user:User = Depends(get_current_user),
    page:int = Query(1,ge=1),
    page_size:int = Query(10,ge=1,le=100)
):
    """
    查询订单列表（订单查询第一步：只看订单主表，分页返回）。

参数说明：
db：数据库异步会话，未登录或 Token 非法时请求进不来。
user：通过 Token 解析出的当前登录用户，只能查到自己名下的订单。
page：当前页码，从 1 开始，小于 1 会被参数校验拦下（422）。
page_size：每页条数，默认 10 条，最多 100 条，防止一次拉太多数据。

功能说明：
获取当前登录用户的 ID，调用 Service 层的 get_orders_service() 分页查询他的订单，
按订单 id 倒序（新下的单排在最前面），只返回订单主表信息
（订单号、总金额、订单状态、下单时间等），不带商品明细；
用户在列表里选中某条订单后，再调用 GET /orders/{order_id} 查看该订单的明细。
该用户没有下过单、或翻到了没有数据的页，返回空列表 []，不算错误；
前端可以用「本次返回条数 < page_size」判断是否已经是最后一页。
"""
    return await get_orders_service(
        user_id=user.id,
        db=db,
        page=page,
        page_size=page_size
    )

@router.get("/orders/{order_id}",response_model=OrderResponse)
async def get_order_api(
    order_id:int,
    db:AsyncSession = Depends(get_session),
    user:User = Depends(get_current_user)
):
    """
    查询订单详情（订单查询第二步：查看某条订单买了什么）。

参数说明：
order_id：要查看的订单 ID，来自第一步订单列表里选中的那条订单。
db：数据库异步会话。
user：通过 Token 解析出的当前登录用户，用于校验订单归属。

功能说明：
调用 Service 层的 get_order_service() 查询订单主表和它的订单明细；
订单不存在、或订单不属于当前登录用户，统一返回 404「订单不存在」，
防止别人拿 order_id 逐个试探出其他人的订单。
查询成功返回订单主表字段 + items（下单时的商品名、单价快照与小计）。
"""
    return await get_order_service(order_id=order_id,user_id=user.id,db=db)

@router.patch("/orders/{order_id}/status",response_model=OrderResponse)
async def update_order_status_api(
    order_id:int,
    data:OrderStatusUpdate,
    db:AsyncSession = Depends(get_session),
    user:User = Depends(get_current_user)
):
    """
    修改订单状态（订单状态流转：付款 / 发货 / 完成 / 取消）。

    参数说明：
    order_id：要修改的订单 ID。
    data：目标状态，1=待付款 2=已付款 3=已发货 4=已完成 5=已取消。
    db：数据库异步会话。
    user：通过 Token 解析出的当前登录用户，用于校验订单归属。

    功能说明：
    调用 Service 层的 update_order_status_service() 修改订单状态：
    1. 订单不存在、或订单不属于当前登录用户 → 404「订单不存在」；
    2. 状态流转不合法（例如「已完成」改回「待付款」）→ 400，提示里带中文状态名；
    3. 改成「已取消」时，下单时扣掉的库存与销量会自动归还商品表；
    4. 修改成功后返回订单主表字段 + items（与创建订单、订单详情的返回结构一致）。

    管理员要改别人的订单，请用 PATCH /admin/orders/{order_id}/status。
    """
    return await update_order_status_service(
        order_id=order_id,
        data=data,
        user_id=user.id,
        db=db
    )
