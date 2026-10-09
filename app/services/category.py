from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.CRUD.category import category_create, category_delete, category_get, category_get_by_name, category_list, category_product_count, category_update
from app.schemas.category import CategoryCreate, CategoryUpdate

async def category_get_service (category_id:int,db:AsyncSession):
    """根据分类id查询分类 查不到返回404"""
    category = await category_get(category_id,db)
    if category is None:
        raise HTTPException(
            status_code=404,
            detail="分类不存在"
        )
    return category

async def category_create_service(data:CategoryCreate,db:AsyncSession):
    """创建分类"""
    category = await category_get_by_name(data.name,db)
    if category is not None:
        raise HTTPException(
            status_code=400,
            detail="分类名称已存在"
        )
    return  await category_create(data,db)

async def category_update_service(category_id:int,data:CategoryUpdate,db:AsyncSession):
    """根据分类 ID 修改分类，修改前检查分类是否存在以及名称是否重复。"""
    category = await category_get_service(category_id,db)
    if data.name is not None:
        #查询是否存在相同名称的分类
        other_category = await category_get_by_name(data.name,db)
        if other_category is not None and category.id != other_category.id:
            raise HTTPException(
                status_code=400,
                detail="分类名称已存在"
            )
    return await category_update(category_id,data,db)

async def category_delete_service(category_id:int,db:AsyncSession):
    """根据分类id删除分类 找不到返回404"""
    await category_get_service(category_id,db)
    #查看该分类下的商品数量（有商品就不能删，没商品才删）
    product_count = await category_product_count(category_id,db)
    if product_count>0:
        raise HTTPException(
            status_code=400,
            detail="该分类下还有商品，无法删除"
    )
    return await category_delete(category_id,db)

async def category_list_service(db:AsyncSession):
    """查询全部分类"""
    return await category_list(db)