from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CartItemCreate(BaseModel):
    """
用于创建购物车商品的数据模型。

product_id：要加入购物车的商品 ID。
quantity：加入购物车的数量，默认为 1，且不能小于 1。
"""
    product_id:int 
    quantity:int =Field(ge=1,default=1)


class CartItemUpdate(BaseModel):
    """
用于修改购物车商品数量的数据模型。

quantity：修改后的商品数量，必须大于等于 1。
"""
    quantity:int = Field(ge=1)


class CartItemResponse(BaseModel):
    """
用于返回购物车商品信息的数据模型。

product_id：商品 ID。
quantity：购物车中该商品的数量。
created_at：加入购物车的时间。
product_name：商品名称。
price：商品单价。
stock：商品当前库存。
status：商品状态，例如 1 表示在售。
subtotal：该商品的小计金额，即商品单价 × 数量。
"""
    product_id:int
    quantity:int
    created_at:datetime
    product_name:str
    price:Decimal
    stock:int
    status:int
    subtotal:Decimal

    model_config=ConfigDict(from_attributes=True)