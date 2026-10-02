from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import CartItem, Product
from app.schemas.cart import CartItemCreate

#查询某用户的某个商品
async def cart_get(user_id:int,product_id:int,db:AsyncSession):
    """
根据用户 ID 和商品 ID 查询购物车商品。
"""
#CartItemResponse 里面同时需要“购物车信息”和“商品信息”
    result = await db.execute(
        select(CartItem,Product)
        .join(Product,CartItem.product_id == Product.id)
        .where(
            CartItem.user_id == user_id,
            CartItem.product_id == product_id
        )
    )
    return result.first()

#查询某用户的全部商品
async def cart_list(user_id:int,db:AsyncSession):
    """
查询指定用户的全部购物车商品。
"""
    result = await db.execute(
        select(CartItem,Product)
        .join(Product,CartItem.product_id == Product.id)
        .where(
            CartItem.user_id == user_id
        )
    )
    return result.all()

#添加购物车商品
async def cart_create(user_id:int,data:CartItemCreate,db:AsyncSession):
    """
创建购物车商品记录。
"""
    cart_item = CartItem(
        user_id =user_id,
        product_id = data.product_id,
        quantity = data.quantity
    )
    db.add(cart_item)
    await db.commit()
    await db.refresh(cart_item)

    return cart_item

#修改购物车商品
async def cart_update(
        item:CartItem,
        quantity:int,
        db:AsyncSession
):
    """
修改购物车商品数量。
"""
    item.quantity = quantity

    await db.commit()
    await db.refresh(item)

    return item
    
#删除购物车商品
async def cart_delete(user_id:int,product_id:int,db:AsyncSession):
    """
删除指定用户的购物车商品。
"""
    # cart_get() 现在返回 (CartItem, Product)，这里只需要 CartItem 本身
    cart, _product = await cart_get(user_id,product_id,db)
    await db.delete(cart)

    await db.commit()
    return cart

#清空购物车
async def cart_clear(user_id:int,db:AsyncSession,commit:bool=True):
    """
清空指定用户的购物车。

commit：删除后是否立即提交事务。
默认 True，保持「清空购物车」接口原有行为（自己提交）；
下单流程传 False，把删购物车并入下单的同一个事务，
由 Service 层统一 commit / rollback，避免订单和购物车状态不一致。
"""
    await db.execute(
        delete(CartItem).where(
            CartItem.user_id == user_id
        )
    )
    if commit:
        await db.commit()
