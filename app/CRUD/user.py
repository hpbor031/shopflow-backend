
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.schemas.user import UserCreate, UserUpdate
from app.core.security import hash_password
from app.models.models import User


async def user_create(user: UserCreate, db: AsyncSession):
    """
    创建用户：用户名 / 邮箱任一重复返回 409，密码只存 bcrypt 哈希，不存明文。

    :return: 入库后的 User 对象（含自增 id、created_at 等）
    """
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
    '''
    按用户名查询用户，登录时用来取出密码哈希做比对。
    查不到返回 None，由 Service 层决定返回什么错误。
    '''
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

async def user_update(user_id:int,user:UserUpdate,db:AsyncSession):
    '''
    修改用户信息
    1. 检查用户是否存在
    2. 检查用户名或邮箱是否已存在
    3. 修改用户信息
    '''
    user_obj = await get_user_by_id(user_id,db)
    if user_obj is None:
        raise HTTPException(
            status_code=404,
            detail="用户不存在"
        )
    _text = []
    if user.username is not None:
        _text.append(User.username == user.username)
    if user.email is not None:
        _text.append(User.email == user.email)
    if _text:
        _sql = select(User).where(User.id!=user_id,or_(*_text))
        result = await db.execute(_sql)
        if result.scalars().first() is not None:
            raise HTTPException(
                status_code=409,
                detail="用户名或邮箱已存在"
            )
        if user.username is not None:
            user_obj.username = user.username
        if user.email is not None:
            user_obj.email = user.email
        try:
            await db.commit()
            await db.refresh(user_obj)
            return user_obj
        except IntegrityError:
            raise HTTPException(status_code=409, detail="用户名或邮箱已存在")
    return user_obj

async def update_user_password(user:User,password:str,db:AsyncSession):
    '''
    修改用户密码
    只更新 `password_hash` 后 commit
    '''
    user.password_hash = hash_password(password)
    await db.commit()
    await db.refresh(user)
    return user

async def get_users(db:AsyncSession,page:int=1,page_size:int=10):
    '''
    分页查询用户列表（管理模块使用，按 id 升序，先注册的排在前面）。

    只做数据库查询，不做权限判断：是不是管理员由 API 层的依赖把关。
    返回 User 对象列表；响应体由 UserMeResponse 白名单控制，
    没有声明的字段（password_hash）不会被返回。
    '''
    sql = (
        select(User)
        .order_by(User.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(sql)
    return result.scalars().all()

async def update_user_status(user:User,status:int,db:AsyncSession):
    '''
    修改用户状态（1=正常 0=禁用），管理模块使用。

    status 的取值范围由 UserStatusUpdate（ge=0, le=1）在入参处校验。
    禁用后该用户即使持有未过期的 token，也会在 get_current_user 里被 403 拦下。
    '''
    user.status = status
    await db.commit()
    await db.refresh(user)
    return user