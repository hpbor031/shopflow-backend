from decimal import Decimal

from sqlalchemy import Row, select
from sqlalchemy.ext.asyncio import AsyncSession

# 这里操作的是数据库表，用的是 ORM 模型：
# Order = orders 表，OrderItem = order_items 表
# 购物车里的数据（CartItem + Product）由 app.CRUD.cart.cart_list() 提供，不在这里重复查询
from app.models.models import Order, OrderItem

async def create_order(user_id:int,total_amount:Decimal,db: AsyncSession):
    '''
    创建订单主表记录（orders 表）。

    user_id：下单用户 ID。
    total_amount：订单总金额，由 Service 层按购物车明细汇总后传进来。
    db：数据库异步会话。

    新订单的 status 走模型默认值 1（待付款），
    商品明细、库存扣减由 Service 层在拿到订单 id 后继续完成。

    只 flush 不 commit：事务边界由 Service 层的下单流程统一管理，
    保证订单、订单明细、库存扣减、清空购物车要么一起生效，要么一起回滚。
    '''
    Order_obj = Order(user_id=user_id, total_amount=total_amount)
    db.add(Order_obj)
    # flush：INSERT 立刻发给数据库，自增 id 回填到对象上，但事务保持打开不提交
    await db.flush()
    await db.refresh(Order_obj)
    return Order_obj

async def create_order_items(order_items:list[OrderItem],db:AsyncSession):
    """
    根据用户当前购物车，为指定订单批量创建订单明细。

    order_items:要创建的订单明细列表。
    db:数据库异步会话。

    商品名和单价在这里做快照保存：
    商品后续改名或改价，都不会影响已经下单的历史订单。

    只 flush 不 commit：事务边界由 Service 层的下单流程统一管理。
    """
    if not order_items:
        raise ValueError("订单明细列表不能为空")
    # 一次性写入全部明细，减少与数据库的交互次数
    db.add_all(order_items)
    await db.flush()
    # 回查自增 id，保证返回的对象带有数据库生成的 id
    for order_item in order_items:
        await db.refresh(order_item)
    return order_items    


async def update_product_stock(cart_items:list[Row],db:AsyncSession):
    """
    下单成功后扣减商品库存、累加商品销量。

    cart_items：cart_list() 返回的 [(CartItem, Product), ...]。
    Product 对象已经加载在当前会话里（与 Service 层用的是同一个 db 会话），
    所以直接改属性再统一提交即可，不必按 product_id 再查一次商品表。

    product.stock -= 购买数量：卖出多少件就减多少库存；
    product.sales += 购买数量：把本次下单的数量记到销量里。
    库存是否充足由 Service 层在下单前校验，这里只负责写入。

    只 flush 不 commit：事务边界由 Service 层的下单流程统一管理。
    """
    for cart, product in cart_items:
        product.stock -= cart.quantity
        product.sales += cart.quantity

    # flush：把本批商品的库存、销量改动发给数据库，是否生效由 Service 层的 commit 决定
    await db.flush()
    return cart_items

async def get_order(order_id:int,db:AsyncSession) -> Order | None:
    """
    根据订单 id 查询订单主表记录。

    order_id：订单 id。
    db：数据库异步会话。

    返回 Order 对象，如果不存在则返回 None。
    """
    return await db.get(Order, order_id)

async def get_orders(user_id:int,db:AsyncSession,page:int=1,page_size:int=10) -> list[Order]:
    """
    根据用户 id 分页查询该用户的订单（新订单在前）。

    user_id：用户 id。
    db：数据库异步会话。
    page：当前页码，从 1 开始，默认第 1 页。
    page_size：每页条数，默认 10 条。

    返回该用户当前页的订单列表，没有订单则返回空列表。
    page / page_size 的合法性（是否小于 0、是否超过上限）由 API 层的 Query(ge=..., le=...) 把关。
    """
    sql = (
        select(Order)
        .where(Order.user_id == user_id)
        # 按主键倒序：id 越大代表下单越晚，新订单排在最前面
        .order_by(Order.id.desc())
        # 分页：先跳过前面 (page - 1) 页的数据，再取本页的 page_size 条
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(sql)
    return result.scalars().all()

async def get_order_items(order_id:int,db:AsyncSession) -> list[OrderItem] | None:
    """
    根据订单 id 查询订单明细表记录。

    order_id：订单 id。
    db：数据库异步会话。

    返回 OrderItem 列表，如果订单不存在则返回空列表。
    """
    sql = select(OrderItem).where(OrderItem.order_id == order_id)
    result = await db.execute(sql)
    return result.scalars().all()

