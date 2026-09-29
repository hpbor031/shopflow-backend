from dataclasses import Field

from pydantic import BaseModel, Field


class OrderItem(BaseModel):
    '''
    添加商品到订单
    '''
    product_id: int = Field(..., title="商品id", description="商品id")
    quantity: int = Field(1, ge=1,le=99)