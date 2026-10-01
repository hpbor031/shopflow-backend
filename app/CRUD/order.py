from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.CRUD.cart import cart_list
from app.schemas.order import OrderItem
# ORM 模型 OrderItem 与 schemas.order.OrderItem 重名，这里用别名区分
from app.models.models import CartItem, Order, OrderItem
async def create_order(user_id:int,total_amount:Decimal,db: AsyncSession):
    '''
    根据用户现有的购物车创建订单
    '''
    Order_obj = Order(user_id=user_id, total_amount=total_amount)
    db.add(Order_obj)
    await db.commit()
    await db.refresh(Order_obj)
    return Order_obj

async def create_order_items(user_id:int,order_id:int,db:AsyncSession):
    """
    根据用户当前购物车，为指定订单批量创建订单明细。

    user_id：下单用户 ID，用于取出该用户购物车里的商品。
    order_id：已经创建好的订单 ID，作为订单明细的外键。
    db：数据库异步会话。

    商品名和单价在这里做快照保存：
    商品后续改名或改价，都不会影响已经下单的历史订单。
    """
    # 取出 [(CartItem, Product), ...]，作为订单明细的数据来源
    cart_items = await cart_list(user_id,db)
    if not cart_items:
        # 购物车为空，没有明细需要写入
        return []

    order_items = [
        OrderItem(
            order_id = order_id,
            product_id = product.id,
            product_name = product.name,#商品名快照
            price = product.price,#下单时的单价快照
            quantity = cart.quantity
        )
        for cart, product in cart_items
    ]

    # 一次性写入全部明细，减少与数据库的交互次数
    db.add_all(order_items)
    await db.commit()
    # 回查自增 id，保证返回的对象带有数据库生成的 id
    for order_item in order_items:
        await db.refresh(order_item)
    return order_items    
