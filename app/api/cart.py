from fastapi import APIRouter,Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.core.database import get_session
from app.models.models import User
from app.schemas.cart import CartItemCreate, CartItemResponse, CartItemUpdate
from app.services.cart import add_to_cart, clear_to_cart, delete_to_cart, list_to_cart, update_to_cart

router = APIRouter()

@router.post("/cart",response_model=CartItemResponse)
async def post_cart(
    data:CartItemCreate,
    db:AsyncSession=Depends(get_session),
    current_user:User = Depends(get_current_user)
):
    """
    添加商品到当前登录用户的购物车。

    data：前端传入的商品 ID 和购买数量。
    current_user：通过 Token 获取当前登录用户。
    db：数据库异步会话。

    功能说明：
    获取当前登录用户的 ID，
    调用 Service 层的 add_to_cart() 完成添加购物车业务。
    """
    return await add_to_cart(
        user_id=current_user.id,
        data=data,
        db=db
    )

@router.put("/cart/{product_id}",response_model=CartItemResponse)
async def update_cart(
    product_id :int,
    data:CartItemUpdate,
    db:AsyncSession = Depends(get_session),
    current_user:User = Depends(get_current_user)
):
    """
修改当前登录用户购物车中的商品数量。

product_id：要修改数量的商品 ID。
data：前端传入的修改后商品数量。
current_user：通过 Token 获取当前登录用户。
db：数据库异步会话。

功能说明：
获取当前登录用户的 ID，
调用 Service 层的 update_to_cart()，
修改指定商品在购物车中的数量。
"""
    return await update_to_cart(product_id=product_id,data=data,db=db,user_id=current_user.id)

@router.delete("/cart/{product_id}",response_model=CartItemResponse)
async def delete_cart(
    product_id:int,
    db:AsyncSession=Depends(get_session),
    current_user:User = Depends(get_current_user)
):
    """删除当前登录用户购物车中的物品"""
    return await delete_to_cart(product_id=product_id,db=db,user_id=current_user.id)

@router.get("/cart",response_model=list[CartItemResponse])
async def get_list_cart(
    db:AsyncSession=Depends(get_session),
    current_user:User = Depends(get_current_user)
):
    """查询当前登录用户购物车中的全部物品"""
    return await list_to_cart(user_id=current_user.id,db=db)

@router.delete("/cart")
async def clear_cart(
    db:AsyncSession=Depends(get_session),
    current_user:User = Depends(get_current_user)
):
    """删除当前登录用户购物车中的全部物品"""
    return await clear_to_cart(user_id=current_user.id,db=db)