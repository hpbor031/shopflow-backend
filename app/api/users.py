from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.services.user import register_user
from app.schemas.user import UserCreate

router = APIRouter()

@router.post('/users/register')
async def register(user:UserCreate,db:AsyncSession = Depends(get_session)):
    result = await register_user(user,db)
    return result
    