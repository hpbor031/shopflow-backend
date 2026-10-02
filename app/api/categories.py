from fastapi import APIRouter,Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.core.database import get_session
from app.models.models import User
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate
from app.services.category import category_create_service, category_delete_service, category_get_service, category_list_service, category_update_service

router = APIRouter()

@router.get("/categories",response_model=list[CategoryOut])
async def get_categories(
    db:AsyncSession = Depends(get_session),
    _current_user:User = Depends(get_current_user)):
    """查询全部分类"""
    return await category_list_service(db)

@router.get("/categories/{category_id}",response_model=CategoryOut)
async def get_category(
    category_id:int,
    db:AsyncSession = Depends(get_session),
    _current_user:User = Depends(get_current_user)):
    """根据分类ID查询分类"""
    return await category_get_service(category_id,db)

@router.post("/categories",response_model=CategoryOut)
async def create_category(
    data:CategoryCreate,
    db:AsyncSession = Depends(get_session),
    _current_user:User = Depends(get_current_user)):
    """创建分类"""
    return await category_create_service(data,db)

@router.put("/categories/{category_id}",response_model=CategoryOut)
async def update_category(
    category_id:int,
    data:CategoryUpdate,
    db:AsyncSession= Depends(get_session),
    _current_user:User = Depends(get_current_user)):
    """修改分类"""
    return await category_update_service(category_id,data,db)

@router.delete("/categories/{category_id}",response_model=CategoryOut)
async def delete_category(
    category_id:int,
    db:AsyncSession= Depends(get_session),
    _current_user:User = Depends(get_current_user)
):
    """删除分类"""
    return await category_delete_service(category_id,db)