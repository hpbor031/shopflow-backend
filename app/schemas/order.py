
"""
订单模块的数据模型（Pydantic v2）。

创建订单接口没有请求体：买什么来自当前登录用户的购物车，买家的身份来自 Token，
所以这个文件只定义「后端返回给客户端」的订单数据结构。
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class OrderItemResponse(BaseModel):
    """
    订单明细（下单时的商品快照）。

id：订单明细 ID。
product_id：商品 ID。
product_name：下单时的商品名快照，商品后续改名不影响历史订单。
price：下单时的商品单价快照，商品后续改价不影响历史订单。
quantity：购买数量。
subtotal：该条明细的小计金额，即 下单时单价 × 购买数量。
"""

    id: int
    product_id: int
    product_name: str
    price: Decimal
    quantity: int
    subtotal: Decimal

    # from_attributes=True：允许 Pydantic 直接从 SQLAlchemy 对象的属性读取数据
    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    """
    订单主表 + 订单明细

id：订单 ID。
user_id：下单用户 ID。
total_amount：订单总金额，由全部订单明细汇总得到。
status：订单状态，1=待付款 2=已付款 3=已发货 4=已完成 5=已取消（新建订单为 1）。
created_at：下单时间。
updated_at：订单最后更新时间。
items：该订单包含的全部订单明细。
"""

    id: int
    user_id: int
    total_amount: Decimal
    status: int
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)


class OrderListItemResponse(BaseModel):
    """
    订单列表里的单条订单（订单查询第一步使用，只返回订单主表，不含订单明细）。

id：订单 ID。
user_id：下单用户 ID。
total_amount：订单总金额。
status：订单状态，1=待付款 2=已付款 3=已发货 4=已完成 5=已取消。
created_at：下单时间。
updated_at：订单最后更新时间。

列表里不返回 items：订单多的时候没必要把每条订单的商品明细都带出来，
用户点开某条订单后，再用 GET /orders/{order_id} 查询该订单的明细。
"""

    id: int
    user_id: int
    total_amount: Decimal
    status: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderStatusUpdate(BaseModel):
    """
    修改订单状态的请求体。

    用户端 PATCH /orders/{order_id}/status
    管理端 PATCH /admin/orders/{order_id}/status
    两个接口共用这个模型。

status：目标状态，1=待付款 2=已付款 3=已发货 4=已完成 5=已取消。

这里只保证取值范围合法；「能不能从当前状态流转到目标状态」由 Service 层的状态机判断，
非法流转返回 400，例如「已完成」的订单不允许再改回「待付款」。
"""

    status: int = Field(
        ge=1,
        le=5,
        description="目标订单状态：1=待付款 2=已付款 3=已发货 4=已完成 5=已取消",
    )

