from fastapi import APIRouter,Depends, Query
from app.api.deps import get_current_user
from app.core.database import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import User
from app.schemas.product import ProductCreate, ProductOut, ProductUpdate
from app.services.product import create_product_service, delete_product_service, get_product_service, list_product_service, update_product_service

router = APIRouter()

#把 CRUD 层查询出来的商品列表，返回给前端/客户端
@router.get("/products",response_model=list[ProductOut])    # 返回的为多个商品列表
async def get_products(
    db:AsyncSession = Depends(get_session),
    keyword:str |None = None,
    category_id :int |None = None,
    status:int|None = None,
    sort_by:str="created_at",
    order:str="desc",
    page:int = Query(1,ge = 1),
    page_size:int = Query(10,ge = 1,le = 100)
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
    products = await list_product_service(
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
    """
根据商品 ID 查询商品详情。
参数说明：
product_id：需要查询的商品 ID。
db：数据库异步会话。
功能说明：接收前端传入的商品 ID，调用 Service 层的 get_product_service() 查询商品信息。
如果商品存在，则返回商品详情；
如果商品不存在，则由 Service 层返回 404 错误。
"""
    product = await get_product_service(product_id,db)
    return product

@router.post("/products",response_model=ProductOut)
async def post_product(
    product:ProductCreate ,
    db:AsyncSession=Depends(get_session),
    _:User = Depends(get_current_user)#这里 _ 表示：我只需要验证 Token 是否有效，不需要使用用户信息。
    ):
    """
创建新的商品。
参数说明：
product：前端传入的商品信息，包括分类、名称、价格、库存等。
current_user：通过 JWT Token 获取当前登录用户。
db：数据库异步会话。
功能说明：验证用户登录状态后，接收前端提交的商品数据，调用 Service 层的 create_product_service() 完成商品创建。创建成功后返回新增商品信息。"""
    product_obj = await create_product_service(product,db)
    return product_obj

@router.put("/products/{product_id}",response_model=ProductOut)
async def put_product(
    product_id:int, 
    product: ProductUpdate,
    db:AsyncSession = Depends(get_session),
    _:User = Depends(get_current_user)
    ):
    """
修改指定商品信息。
参数说明：
product_id：需要修改的商品 ID。
product：前端传入需要更新的商品字段。
current_user：通过 JWT Token 获取当前登录用户。
db：数据库异步会话。
功能说明：
验证用户登录状态后，根据商品 ID 查找目标商品，调用 Service 层的 update_product_service()完成商品信息更新。
更新成功后返回修改后的商品数据。
"""
    product_obj = await update_product_service(product_id,product,db)
    return product_obj

@router.delete("/products/{product_id}",response_model=ProductOut)
async def delete_product(
    product_id:int, 
    db:AsyncSession = Depends(get_session),
    _:User = Depends(get_current_user)
    ):
    """
下架指定商品。
功能说明：验证用户登录状态后，根据商品 ID 查询目标商品，
调用 Service 层的 delete_product_service()将商品状态修改为下架状态。
注意：
当前实现采用软删除方式，
不会真正删除数据库中的商品记录，
而是修改商品 status 字段。
"""
    product_obj = await delete_product_service(product_id,db)
    return product_obj