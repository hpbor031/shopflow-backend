from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Category, Product
from app.schemas.category import CategoryCreate, CategoryUpdate

async def category_get(category_id:int,db:AsyncSession):
    """
根据分类 ID 查询分类。

查询成功返回 Category 对象。
查询不到返回 None。
"""
    sql = select(Category).where(Category.id==category_id)
    result = await db.execute(sql)
    return result.scalar_one_or_none()

async def category_get_by_name(name:str,db:AsyncSession):
    """
根据分类名称查询分类。

查询成功返回 Category 对象。
查询不到返回 None。
"""
    sql = select(Category).where(Category.name ==name)
    result = await db.execute(sql)
    return result.scalar_one_or_none()

async def category_create(category_data:CategoryCreate,db:AsyncSession):
    """
创建一个新的分类。

创建成功返回 Category 对象。
"""
    category_obj = Category(name = category_data.name)
    db.add(category_obj)
    await db.commit()
    await db.refresh(category_obj)
    return category_obj

async def category_update(category_id:int,category_data:CategoryUpdate,db:AsyncSession):
    """
    根据分类 ID 修改分类。

    找不到分类时返回 None。
    修改成功返回 Category 对象。
    """
    category_obj = await category_get(category_id,db)
    if category_obj is None:
        return None
    update_data = category_data.model_dump(#把用户真正要修改的字段提取出来
        exclude_unset=True,#只保留用户这一次请求中真正传过来的字段
        exclude_none=True#如果字段的值是 None，就把它排除掉
    )
    for key,value in update_data.items():
        #setattr(根据变量指定的属性名，给对象设置一个新值)
        setattr(category_obj,key,value)

    await db.commit()
    await db.refresh(category_obj)
    return category_obj

async def category_delete(category_id:int,db:AsyncSession):
    """
根据分类 ID 删除分类。

找不到分类时返回 None。
"""
    category_obj =await category_get(category_id,db)
    if category_obj is None:
        return None
    await db.delete(category_obj)

    await db.commit()
    return category_obj

async def category_list(db:AsyncSession):
    """查询所有分类"""
    sql = select(Category)
    result = await db.execute(sql)
    return result.scalars().all()

async def category_product_count(category_id:int,db:AsyncSession):
    """统计指定分类下的商品数量"""
    sql = (select(func.count(Product.id))
           .where(Product.category_id == category_id) 
    )   
    result = await db.execute(sql)
    return result.scalar()
