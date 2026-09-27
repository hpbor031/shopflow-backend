from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.CRUD.user import get_user_by_username, user_create,user_update
from app.core.security import create_access_token, verify_password
from app.schemas.user import UserCreate, UserLogin,UserUpdate

async def register_user(user: UserCreate,db:AsyncSession):
    '''
    调用user_create函数创建用户
    '''
    user_obj = await user_create(user,db)
    return user_obj
async def login_user(user:UserLogin,db:AsyncSession):
    
    '''
    校验账号密码，通过后签发 access_token

    两个安全要点：
    1. "用户不存在"和"密码错误"返回完全一样的响应。
    2. status 的判断放在密码校验之后，否则"密码输错的人"也能知道账号存在。
    '''
    user_obj = await get_user_by_username(user.username,db)

    # 用户不存在 或 密码不正确 → 统一 401
    if user_obj is None or not verify_password(user.password,user_obj.password_hash):
        raise HTTPException(status_code=401,detail="用户名或密码错误")
    # 检查账号是否被禁用
    if user_obj.status == 0:
        raise HTTPException(status_code=403,detail="账号已被禁用")
    # 登录只读不写，不需要 commit，事务由 get_session 统一收尾
    return create_access_token(user_id=user_obj.id,username=user_obj.username)

async def update_user_profile(user_id:int,user:UserUpdate,db:AsyncSession):
    '''
    修改当前登录用户个人的信息
    '''
    if user.username is None and user.email is None:
        raise HTTPException(status_code=400,detail="请填写要修改的信息")
    return await user_update(user_id,user,db)