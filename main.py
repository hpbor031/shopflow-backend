"""
应用入口（main.py）

作用：创建 FastAPI 实例、挂载路由，并管理应用启动 / 关闭时要做的事情。
"""
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.database import create_tables,engine
from app.api.users import router as users_router
from app.api.products import router as products_router
from app.api.cart import router as cart_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 生命周期钩子（lifespan）。

    - yield 之前：应用启动时执行，建表（表已存在则自动跳过）
    - yield 之后：应用关闭时执行，释放数据库连接池
    """
    await create_tables()
    yield
    await engine.dispose()
app = FastAPI(lifespan=lifespan)

# 注册用户相关路由（/users/register、/users/login、/users/me）
app.include_router(users_router)
app.include_router(products_router)
app.include_router(cart_router)

@app.get("/")
async def root():
    """根路径探活接口：返回服务名，用于确认后端已正常启动。"""
    return {"message": "ShopFlow Backend"}
