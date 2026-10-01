from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.CRUD.cart import cart_list
from app.CRUD.order import create_order


async def create_order_service(user_id:int,db:AsyncSession):
    """
    创建订单
    1. 获取用户购物车中的商品
    2. 计算总金额
    3. 调用 create_order() 创建订单
    """

    result = await cart_list(user_id,db)
    if not result:
        raise HTTPException(
            status_code=400,
            detail="购物车为空，无法创建订单"
        )
    total_amount = sum(cart.quantity * cart_product.price for cart, cart_product in result)
    return await create_order(user_id, total_amount, db)