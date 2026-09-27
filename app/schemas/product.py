#规定 客户端传给后端的数据长什么样，以及后端返回给客户端的数据长什么样

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict

class ProductCreate(BaseModel):
    category_id:int
    name:str
    description:str | None = None
    price:Decimal
    stock:int
    status:int

class ProductUpdate(BaseModel):
    category_id:int | None = None
    name:str | None = None
    description:str | None = None
    price:Decimal | None = None
    stock:int | None = None
    status:int | None = None

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