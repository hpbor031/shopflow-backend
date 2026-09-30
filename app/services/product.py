#“业务逻辑层”service，负责协调 API 和 CRUD
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.product import ProductCreate,ProductUpdate
from app.CRUD.product import product_get,product_create,product_delete, product_list,product_update

async def get_product_service(product_id:int,db:AsyncSession):
    """查询商品详情，透传 CRUD 层结果。"""
    product_obj =await product_get(product_id,db)
    if product_obj is None:
        raise HTTPException(
                status_code=404,
            detail="商品不存在"
        )
    return product_obj

async def create_product_service(product:ProductCreate,db:AsyncSession):
    """创建商品，透传 CRUD 层结果。"""
    return await product_create(product,db)

async def delete_product_service(product_id:int,db:AsyncSession):
    """删除商品，透传 CRUD 层结果。"""
    product_obj =await product_delete(product_id,db)
    if product_obj is None:
        raise HTTPException(
                status_code=404,
            detail="商品不存在"
        )
    return product_obj

async def update_product_service(product_id:int,product:ProductUpdate,db:AsyncSession):
    """修改商品，透传 CRUD 层结果。"""
    product_obj = await product_update(product_id,product,db)
    if product_obj is None:
        raise HTTPException(
                status_code=404,
            detail="商品不存在"
        )
    return product_obj

async def list_product_service(
    db: AsyncSession,
    keyword: str | None = None,
    category_id: int | None = None,
    status: int | None = None,
    sort_by: str = "created_at",
    order: str = "desc",
    page: int = 1,
    page_size: int = 10
):
    """查询商品列表，透传 CRUD 层结果。"""

    products= await product_list(
        db,
        keyword=keyword,
        category_id=category_id,
        status=status,
        sort_by=sort_by,
        order=order,
        page=page,
        page_size=page_size
    )
    if products is None:
        raise HTTPException(
            status_code=400,
            detail="排序参数错误"
        )
    return products