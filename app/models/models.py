from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column
from sqlalchemy import DateTime,func,String,Float,ForeignKey
from datetime import datetime

# 创建基类
class Base(DeclarativeBase):
    created_at:Mapped[datetime] = mapped_column(DateTime,default=func.now())
    updated_at:Mapped[datetime] = mapped_column(DateTime,default=func.now(),onupdate=func.now())
# user表结构
class User(Base):
    __tablename__ = 'user'
    id:Mapped[int] = mapped_column(primary_key=True,autoincrement=True)
    username:Mapped[str] = mapped_column(String(20),nullable=True)
    gender:Mapped[str] = mapped_column(String(20))
    password:Mapped[str] = mapped_column(String(20))
    email:Mapped[str] = mapped_column(String(20))
    phone:Mapped[str] = mapped_column(String(20),unique=True)

# product表结构
class Product(Base):
    __tablename__ = 'product'
    id:Mapped[int] = mapped_column(primary_key=True,autoincrement=True)
    name:Mapped[str] = mapped_column(String(20))
    price:Mapped[float] = mapped_column(Float)
    num:Mapped[int] = mapped_column()

# order表结构
class Order(Base):
    __tablename__ = 'order'
    id:Mapped[int] = mapped_column(primary_key=True,autoincrement=True)
    user_id:Mapped[int] = mapped_column(ForeignKey('user.id'))
    product_id:Mapped[int] = mapped_column(ForeignKey('product.id'))
    num:Mapped[int] = mapped_column()
    price:Mapped[float] = mapped_column(Float)
