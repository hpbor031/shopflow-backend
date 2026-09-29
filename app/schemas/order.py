from fastapi import Query
from pydantic import BaseModel


class OrderItem(BaseModel):
    '''
    添加商品到订单
    '''
    product_id: int = Query(..., title="商品id", description="商品id")
    quantity: int = Query(1, ge=1,le=99)