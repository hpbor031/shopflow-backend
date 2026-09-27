#“业务逻辑层”service，负责协调 API 和 CRUD
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.product import ProductCreate,ProductUpdate
from app.CRUD.product import product_get,product_create,product_delete,product_update

async def get_product_service(product_id:int,db:AsyncSession):
    return await product_get(product_id,db)

async def create_product_service(product:ProductCreate,db:AsyncSession):
    return await product_create(product,db)

async def delete_product_service(product_id:int,db:AsyncSession):
    return await product_delete(product_id,db)

async def update_product_service(product_id:int,product:ProductUpdate,db:AsyncSession):
    return await product_update(product_id,product,db)