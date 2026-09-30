#规定 客户端传给后端的数据长什么样，以及后端返回给客户端的数据长什么样

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

class ProductCreate(BaseModel):
    category_id:int
    name:str = Field(min_length=1,max_length=100,description="商品名称")
    description:str | None = None
    price:Decimal=Field(gt=0)
    stock:int=Field(ge=0)
    status:int=Field(ge=0,le=1)

class ProductUpdate(BaseModel):
    category_id:int | None = None
    name:str | None = Field(default=None,min_length=1,max_length=100)
    description:str | None = None
    price:Decimal | None = Field(default=None,ge=0)
    stock:int | None = Field(default=None,gt=0)
    status:int | None = Field(default=None,ge=0,le=1)

class ProductOut(BaseModel):
    id:int
    category_id:int
    name:str
    description:str | None = None
    price:Decimal
    stock:int
    sales:int
    status:int
    created_at:datetime
    updated_at:datetime


#from_attributes=True 就是告诉 Pydantic：
#可以从 SQLAlchemy 对象的属性里面读取数据，转换成这个响应模型。
    model_config=ConfigDict(from_attributes=True)