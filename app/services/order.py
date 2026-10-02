from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.CRUD.cart import cart_clear, cart_list
from app.CRUD.order import create_order, create_order_items, get_order, get_order_items, get_orders, update_product_stock
from app.models.models import Order, OrderItem


def build_order_item(order_item:OrderItem) -> dict:
    """
    把 ORM 的 OrderItem 组装成 OrderItemResponse 需要的数据。

    除 subtotal 外的字段都来自 order_items 表（下单时写入的快照），
    小计 subtotal = 下单时单价 × 购买数量。
    """
    return {
        "id": order_item.id,
        "product_id": order_item.product_id,
        "product_name": order_item.product_name,
        "price": order_item.price,
        "quantity": order_item.quantity,
        "subtotal": order_item.price * order_item.quantity
    }


def build_order(order:Order,order_items:list[OrderItem]) -> dict:
    """
    把 ORM 的订单主表记录 + 它的订单明细，组装成 OrderResponse 需要的数据。

    order：orders 表的 ORM 对象。
    order_items：该订单在 order_items 表里的全部明细。

    创建订单和查询订单详情共用这一份组装逻辑，
    保证「下单返回的订单」和「查询返回的订单」结构完全一致。
    """
    return {
        "id": order.id,
        "user_id": order.user_id,
        "total_amount": order.total_amount,
        "status": order.status,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "items": [
            build_order_item(order_item)
            for order_item in order_items
        ]
    }


async def create_order_service(user_id:int,db:AsyncSession):
    """
    创建订单（下单主流程）。

    user_id：下单用户 ID，由 API 层从 Token 中取出。
    db：数据库异步会话。

    步骤：
    1. 取出用户购物车里的商品（购物车是下单的唯一数据来源，购物车为空直接 400）；
    2. 逐件校验：商品必须在上架状态，购买数量不能超过当前库存；
    3. 汇总订单总金额 total_amount = Σ(商品单价 × 购买数量)；
    4. 开启一个事务，依次执行：写入订单主表（status 为默认的 1=待付款）→
       写入订单明细（商品名、单价做快照）→ 扣减库存并累加销量 → 清空该用户的购物车；
    5. 全部成功才 commit 一次，保证上面 4 步同时生效；
       任何一步抛异常都 rollback，数据库回到下单前的状态，
       不会出现「订单生成了但库存没扣」或「库存扣了但订单没生成」的脏数据；
    6. 提交前先组装好响应数据（提交后 ORM 对象会过期），最后返回「订单主表 + 全部明细」。
    """

    #  购物车里的每一行都带上商品信息：[(CartItem, Product), ...]
    cart_items = await cart_list(user_id,db)
    if not cart_items:
        raise HTTPException(
            status_code=400,
            detail="购物车为空，无法创建订单"
        )

    #  下单前校验：商品下架或库存不足都不允许下单
    for cart, cart_product in cart_items:
        if cart_product.status != 1:
            raise HTTPException(
                status_code=400,
                detail=f"商品「{cart_product.name}」已下架，无法下单"
            )
        if cart.quantity > cart_product.stock:
            raise HTTPException(
                status_code=400,
                detail=f"商品「{cart_product.name}」库存不足，当前库存 {cart_product.stock}"
            )

    #  汇总总金额。金额用 Decimal 计算，起始值也用 Decimal，避免浮点误差
    total_amount = sum(
        (
            cart.quantity * cart_product.price
            for cart, cart_product in cart_items
        ),
        Decimal("0")
    )

    #  下面 4 步写库属于同一笔业务，必须放在同一个事务里：
    #  要么一起成功提交，要么任意一步出错整体回滚，
    #  避免出现「订单生成了但库存没扣」或「库存扣了但订单没生成」的脏数据。
    #  CRUD 层这几个函数只 flush 不 commit，事务边界由这里统一控制。
    try:
        #  创建订单主表记录（flush 后拿到自增的订单 id，供明细使用）
        order = await create_order(user_id, total_amount, db)

        #  创建订单明细。该函数内部会再取一次购物车，保证明细与当前购物车一致
        order_items = await create_order_items_service(user_id, order.id, db)

        #  扣减商品库存、累加商品销量
        await update_product_stock(cart_items, db)

        #  购物车里的商品已经变成订单明细，清空购物车
        #  commit=False：删购物车并入当前事务，不单独提交
        await cart_clear(user_id, db, commit=False)

        #  先组装返回数据再提交：commit 后 ORM 对象会过期，属性读不出来
        #  组装逻辑与「查询订单详情」共用 build_order()，保证两处返回结构一致
        response = build_order(order, order_items)

        #  一次提交：订单、明细、库存、销量、购物车清空同时生效
        await db.commit()
    except Exception:
        #  任何一步失败都整体回滚，数据库回到下单前的状态
        await db.rollback()
        raise

    return response

async def create_order_items_service(user_id:int,order_id:int,db:AsyncSession):
    """
       根据用户当前购物车，为指定订单批量创建订单明细。
   
       user_id：下单用户 ID，用于取出该用户购物车里的商品。
       order_id：已经创建好的订单 ID，作为订单明细的外键。
       db：数据库异步会话。
   
       商品名和单价在这里做快照保存：
       商品后续改名或改价，都不会影响已经下单的历史订单。
    """
    # 取出 [(CartItem, Product), ...]，作为订单明细的数据来源

    cart_items = await cart_list(user_id, db)
    if not cart_items:
        raise HTTPException(
            status_code=400,
            detail="购物车为空，无法创建订单明细"
        )
    order_items = [
        OrderItem(
            order_id = order_id,
            product_id = cart_product.id,
            product_name = cart_product.name,
            price = cart_product.price,
            quantity = cart.quantity
        )
        for cart, cart_product in cart_items
    ]
    return await create_order_items(order_items, db)

async def get_orders_service(user_id:int,db:AsyncSession,page:int=1,page_size:int=10):
    """
       获取当前登录用户的订单列表（分页，只返回订单主表，不含明细）。
   
       user_id：下单用户 ID，用于取出该用户的订单。
       db：数据库异步会话。
       page：当前页码，从 1 开始。
       page_size：每页条数。
   
    """
    # 分页查询：只取当前页的订单，新订单排在前面（分页逻辑在 CRUD 层）
    return await get_orders(user_id, db, page=page, page_size=page_size)

async def get_order_service(order_id:int,user_id:int,db:AsyncSession):
    """
    查询指定订单详情（订单主表 + 订单明细）。

    订单查询的第二步：用户在上一步的订单列表里选中订单后，用这个方法查明细。

    order_id：要查看的订单 ID。
    user_id：当前登录用户 ID，用于校验订单归属，防止越权查看别人的订单。
    db：数据库异步会话。

    订单不存在、或订单不属于当前登录用户，统一返回 404「订单不存在」：
    不区分"订单不存在"和"订单不是你的"，避免别人拿 order_id 逐个试探出其他人的订单。

    明细里存的是下单时的商品名与单价快照，商品后续改名、改价都不会影响这里。
    """
    # 先查订单主表，同时完成归属校验
    order = await get_order(order_id, db)
    if order is None or order.user_id != user_id:
        raise HTTPException(
            status_code=404,
            detail="订单不存在"
        )

    # 再查该订单的全部明细，最后组装成 OrderResponse（订单主表字段 + items）
    order_items = await get_order_items(order_id, db)
    return build_order(order, order_items)
    
