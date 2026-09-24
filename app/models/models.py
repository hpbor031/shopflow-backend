from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# 创建基类
class Base(DeclarativeBase):
    """所有数据表模型的基类，只负责注册元数据，不定义公共字段"""
    pass

# 时间戳混入：拥有 created_at + updated_at 的表复用
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

# 创建时间混入：只需要 created_at 的表复用
class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

# users 用户表
class User(TimestampMixin, Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # 用户名、邮箱都要求唯一，注册时需要判重
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    # 只存 bcrypt 加密后的密码，不存明文
    password_hash: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    # 1=正常 0=禁用
    status: Mapped[int] = mapped_column(Integer, default=1)

# categories 商品分类表
class Category(CreatedAtMixin, Base):
    __tablename__ = 'categories'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # 分类名不允许重复
    name: Mapped[str] = mapped_column(String(50), unique=True)

# products 商品表
class Product(TimestampMixin, Base):
    __tablename__ = 'products'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id'), index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    # 商品描述可以省略
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 金额使用定点数，避免浮点误差
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    # 库存、销量默认从 0 开始
    stock: Mapped[int] = mapped_column(Integer, default=0)
    sales: Mapped[int] = mapped_column(Integer, default=0)
    # 1=上架 0=下架
    status: Mapped[int] = mapped_column(Integer, default=1)

# cart_items 购物车明细表
class CartItem(CreatedAtMixin, Base):
    __tablename__ = 'cart_items'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'), index=True)
    # 同一商品的数量，最少 1 件
    quantity: Mapped[int] = mapped_column(Integer, default=1)

# orders 订单主表
class Order(TimestampMixin, Base):
    __tablename__ = 'orders'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    # 订单总金额，由订单明细汇总得到
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    # 1=待付款 2=已付款 3=已发货 4=已完成 5=已取消
    status: Mapped[int] = mapped_column(Integer, default=1)

# order_items 订单明细表
class OrderItem(Base):
    __tablename__ = 'order_items'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id'), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'), index=True)
    # 下单时的商品名快照，商品后续改名不影响历史订单
    product_name: Mapped[str] = mapped_column(String(100))
    # 下单时的单价快照
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    quantity: Mapped[int] = mapped_column(Integer)
