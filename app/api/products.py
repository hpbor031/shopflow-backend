from fastapi import APIRouter,Depends
from app.core.database import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from app.CRUD.product import product_list

router = APIRouter()

#把 CRUD 层查询出来的商品列表，返回给前端/客户端
@router.get("/products")
async def get_products(
    db:AsyncSession = Depends(get_session),
    keyword:str |None = None,
    category_id :int |None = None,
    status:int|None = None,
    sort_by:str="created_at",
    order:str="desc",
    page:int = 1,
    page_size:int = 10
):
    products = await product_list(
        db,
        keyword= keyword,
        category_id=category_id,
        status=status,
        sort_by=sort_by,
        order=order,
        page=page,
        page_size=page_size
    )
    return products
