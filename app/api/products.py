from fastapi import APIRouter,Depends
from app.core.database import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from app.CRUD.product import product_create, product_delete, product_get, product_list, product_update
from app.schemas.product import ProductCreate, ProductOut, ProductUpdate

router = APIRouter()

#把 CRUD 层查询出来的商品列表，返回给前端/客户端
@router.get("/products",response_model=list[ProductOut])
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
    """
获取商品列表

参数说明：
keyword：商品名称搜索关键词，可选
category_id：商品分类 ID，可选，用于按分类筛选商品
status：商品状态，可选，用于筛选商品状态
sort_by：排序字段，默认按照创建时间排序
order：排序方式，默认降序（desc）
page：当前页码，默认为第 1 页
page_size：每页返回的商品数量，默认为 10 条

功能说明：
根据前端传入的查询条件，调用 CRUD 层的 product_list()
查询数据库中的商品，并将查询结果返回给前端。
"""
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

@router.get("/products/{product_id}",response_model=ProductOut)
async def get_product(product_id:int,db:AsyncSession=Depends(get_session)):
    product = await product_get(product_id,db)
    return product

@router.post("/products",response_model=ProductOut)
async def post_product(product:ProductCreate ,db:AsyncSession=Depends(get_session)):
    product_obj = await product_create(product,db)
    return product_obj

@router.put("/products/{product_id}",response_model=ProductOut)
async def put_product(product_id:int, product: ProductUpdate,db:AsyncSession = Depends(get_session)):
    product_obj = await product_update(product_id,product,db)
    return product_obj

@router.delete("/products/{product_id}",response_model=ProductOut)
async def delete_product(product_id:int, db:AsyncSession = Depends(get_session)):
    product_obj = await product_delete(product_id,db)
    return product_obj