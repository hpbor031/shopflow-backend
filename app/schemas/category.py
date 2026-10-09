from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    """
创建分类时，客户端传入的数据格式。
"""
    name:str = Field(
        min_length=1,
        max_length=50,
        description=" 分类名称"
    )

class CategoryUpdate(BaseModel):
    """
    修改分类时，客户端传入的数据格式。
    """
    name:str |None = Field(
        default=None,
        min_length=1,
        max_length=50,
        description=" 新的分类名称"
    )

class CategoryOut(BaseModel):
    """
    返回给客户端的分类数据格式。
    """
    id:int
    name:str 
    created_at:datetime

    model_config = ConfigDict(from_attributes=True)