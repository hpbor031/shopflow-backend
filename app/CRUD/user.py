from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.schemas.user import UserCreate
from app.core.security import hash_password
from app.models.models import User


async def user_create(user: UserCreate, db: AsyncSession):

    # 检查用户名或邮箱是否已存在
    sql = select(User).where(
        or_(
            User.username == user.username,
            User.email == user.email
        )
    )

    result = await db.execute(sql)
    existing_user = result.scalar_one_or_none()
    if existing_user:
        if existing_user.username == user.username:
            raise HTTPException(
                status_code=409,
                detail="用户名已存在"
            )
        if existing_user.email == user.email:
            raise HTTPException(
                status_code=409,
                detail="邮箱已存在"
            )
    # 密码加密
    password_hash = hash_password(user.password)
    # 创建用户
    user_obj = User(
        username=user.username,
        email=user.email,
        password_hash=password_hash
    )
    try:
        db.add(user_obj)

        await db.commit()
        await db.refresh(user_obj)
        return user_obj
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="用户名或邮箱已存在"
        )

async def get_user_by_username(username:str,db:AsyncSession):
    sql = select(User).where(User.username == username)
    result = await db.execute(sql)
    user = result.scalar_one_or_none()
    return user

async def get_user_by_id(user_id:int,db:AsyncSession):
    '''
    按主键查询用户，供鉴权使用：
    token 的 payload 里只有 user_id，需要拿它换回完整的用户对象。
    '''
    sql = select(User).where(User.id == user_id)
    result = await db.execute(sql)
    user = result.scalar_one_or_none()
    return user
