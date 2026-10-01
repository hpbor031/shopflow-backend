from fastapi import HTTPException

from app.CRUD.cart import cart_clear, cart_create, cart_delete, cart_get, cart_list, cart_update
from app.CRUD.product import product_get
from app.models.models import CartItem, Product
from app.schemas.cart import CartItemCreate, CartItemUpdate
from sqlalchemy.ext.asyncio import AsyncSession


def build_cart_item(cart:CartItem,product:Product) -> dict:
    """
    把 (CartItem, Product) 组装成 CartItemResponse 需要的数据。

    购物车信息（id、product_id、quantity、created_at）来自 CartItem；
    商品信息（product_name、price、stock、status）来自 Product；
    小计 subtotal = 商品单价 × 购物车数量。
    """
    return {
        "id": cart.id,
        "product_id": cart.product_id,
        "quantity": cart.quantity,
        "created_at": cart.created_at,
        "product_name": product.name,
        "price": product.price,
        "stock": product.stock,
        "status": product.status,
        "subtotal": product.price * cart.quantity
    }

async def add_to_cart(user_id:int,data:CartItemCreate,db:AsyncSession):
    """添加商品到购物车。"""
    product = await product_get(data.product_id,db)
    if product is None:
         raise HTTPException(
            status_code=404,
            detail="商品不存在"
        )
    if product.status !=1:
          raise HTTPException(
        status_code=400,
        detail="商品已下架"
    )

    #检查购物车里是否有该商品
    cart_result = await cart_get(user_id,data.product_id,db)
    if cart_result is not None:
        cart, cart_product = cart_result
        new_quantity = cart.quantity + data.quantity
        if new_quantity>cart_product.stock:
            raise HTTPException(
                status_code=400,
                detail="商品库存不足"
    )
        cart.quantity = new_quantity
        await db.commit()
        await db.refresh(cart)

        return build_cart_item(cart,cart_product)

    #购物车里没有该商品：新增数量同样不能超过库存
    if data.quantity>product.stock:
        raise HTTPException(
            status_code=400,
            detail="商品库存不足"
    )
    cart = await cart_create(user_id,data,db)

    return build_cart_item(cart,product)

async def update_to_cart(user_id:int,product_id:int,data:CartItemUpdate,db:AsyncSession):
    """修改购物车商品数量"""
    #cart_get() 现在返回 (CartItem, Product)，商品信息直接从 JOIN 结果里取
    cart_result = await cart_get(user_id,product_id,db)
    if cart_result is None:
        raise HTTPException(
            status_code=404,
            detail="购物车商品不存在"
    )
    cart, product = cart_result
    if data.quantity>product.stock:
        raise HTTPException(
            status_code=400,
            detail="商品库存不足")
    #修改数量
    await cart_update(cart,data.quantity,db)

    return build_cart_item(cart,product)

async def delete_to_cart(user_id:int,product_id:int,db:AsyncSession):
    """删除购物车商品"""
    cart_result = await cart_get(user_id,product_id,db)
    if cart_result is None:
        raise HTTPException(
            status_code=404,
            detail="购物车商品不存在"
    )
    cart, product = cart_result
    #先组装好返回数据再删除，避免删除后对象状态不可用
    response = build_cart_item(cart,product)
    await cart_delete(user_id,product_id,db)

    return response

async def list_to_cart(user_id:int,db:AsyncSession):
    """查询某个用户购物车的全部商品"""
    cart_result_list = await cart_list(user_id,db)

    return [
        build_cart_item(cart,product)
        for cart,product in cart_result_list
    ]

async def clear_to_cart(user_id:int,db:AsyncSession):
    """清空某个用户的购物车"""
    return await cart_clear(user_id,db)