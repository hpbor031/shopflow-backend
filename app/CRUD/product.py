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