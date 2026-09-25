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

    db.add(user_obj)

    await db.commit()
    await db.refresh(user_obj)

    return user_obj