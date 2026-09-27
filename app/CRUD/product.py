#真正负责“操作数据库”的地方

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import Product
from app.schemas.product import ProductCreate,ProductUpdate

#查询商品详情
async def product_get(product_id:int,db:AsyncSession):
    sql = select(Product).where(Product.id ==product_id)
    result = await db.execute(sql)#result查询结果容器
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(
            status_code= 404,
            detail="商品不存在"
        )
    return product

#创建商品
async def product_create(product:ProductCreate,db:AsyncSession):
    product_obj = Product(
        category_id = product.category_id,
        name = product.name,
        description =  product.description,
        price =  product.price,
        stock =  product.stock,
        status =  product.status
    )
    db.add( product_obj )
    await db.commit()
    await db.refresh( product_obj )
    return product_obj 

#修改商品
async def product_update(product_id : int, product:ProductUpdate,db:AsyncSession):
    product_obj = await product_get(product_id,db)
    #model_dump(把 Pydantic 模型对象转换成 Python 字典） exclude_unset(排除没有被设置的)
    update_data = product.model_dump(exclude_unset=True)
    for key,value in update_data.items():
        #setattr(根据变量指定的属性名，给对象设置一个新值)
        setattr(product_obj,key,value)

    await db.commit()
    await db.refresh( product_obj )
    return product_obj 

#删除商品
async def product_delete(product_id : int,db:AsyncSession):
    product_obj = await product_get(product_id,db)
    await db.delete( product_obj )

    await db.commit()
    return product_obj 

#商品列表
async def product_list(       
        db:AsyncSession,
        keyword:str |None = None,
        category_id :int |None = None,
        status:int|None = None,
        sort_by:str="created_at",
        order:str="desc",
        page:int = 1,
        page_size:int = 10
        
):
    """
    # 商品列表
    keyword：商品搜索关键词
    page：当前页码
    page_size：每页返回的商品数量
    category_id：商品分类 ID，用于按分类筛选商品
    status：商品状态，用于筛选上架、下架等状态的商品
    sort_by：排序字段，例如价格、销量、创建时间等
    order：排序方式，例如升序（asc）或降序（desc）
    """

    #根据搜索关键字、商品分类、商品状态筛选商品
    sql = select(Product)
    if keyword:
        sql = sql.where(Product.name.like(f"%{keyword}%"))
    if category_id:
        sql = sql.where(Product.category_id == category_id)
    if status is not None:
        sql = sql.where(Product.status == status)

    #确定排序字段并排序
    sort_column = getattr(Product,sort_by)
    if order == "asc":
        sql= sql.order_by(sort_column.asc())
    else:
        sql= sql.order_by(sort_column.desc())

    #分页
    offset = (page-1)*page_size#计算需要跳过的商品数量
    sql = sql.offset(offset).limit(page_size)#(先跳过 offset 条商品，然后拿 page_size 条商品
    
    result = await db.execute(sql)
    products = result.scalars().all()
    return products