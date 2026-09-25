from sqlalchemy.ext.asyncio import AsyncSession

from app.CRUD.user import user_create
from app.schemas.user import UserCreate

async def register_user(user: UserCreate,db:AsyncSession):
    '''
    调用user_create函数创建用户
    '''
    user_obj = await user_create(user,db)
    return user_obj
    