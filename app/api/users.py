from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.services.user import login_user, register_user
from app.schemas.user import TokenResponse, UserCreate, UserLogin, register_response

router = APIRouter()

@router.post('/users/register',response_model=register_response,status_code=201)
async def register(user:UserCreate,db:AsyncSession = Depends(get_session)):
    result = await register_user(user,db)
    return result

@router.post('/users/login',response_model=TokenResponse)
async def login(user:UserLogin,db:AsyncSession = Depends(get_session)):
    # Service 交回的是纯 token 字符串，"响应体长什么样"属于接口协议，由 API 层组装
    token = await login_user(user,db)
    return {"access_token": token, "token_type": "bearer"}
        