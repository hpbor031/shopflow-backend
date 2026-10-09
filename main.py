"""
应用入口（main.py）

作用：创建 FastAPI 实例、挂载路由，并管理应用启动 / 关闭时要做的事情。
"""
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
import time

from app.core.database import create_tables,engine
from app.core.exceptions import register_exception_handlers
from app.core.logger import get_logger, setup_logging
from app.api.users import router as users_router
from app.api.products import router as products_router
from app.api.cart import router as cart_router
from app.api.categories import router as categories_router
from app.api.order import router as order_router
from app.api.admin import router as admin_router

# 日志初始化必须放在最前面：之后各模块 get_logger() 拿到的 logger 才有统一的格式与输出目标
setup_logging()
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 生命周期钩子（lifespan）。

    - yield 之前：应用启动时执行，建表（表已存在则自动跳过）
    - yield 之后：应用关闭时执行，释放数据库连接池
    """
    logger.info("ShopFlow Backend 启动中：开始检查数据库表结构")
    await create_tables()
    logger.info("数据库表检查完成，服务已就绪")
    yield
    await engine.dispose()
    logger.info("ShopFlow Backend 已关闭：数据库连接池已释放")

app = FastAPI(lifespan=lifespan)

# 注册全局异常处理器：业务异常、参数校验失败、未捕获异常统一成同一种 JSON 结构
register_exception_handlers(app)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    请求日志中间件：记录每个请求的方法、路径、响应状态码与耗时。

    排查问题时先看这一行，能快速定位「是哪个接口、慢不慢、返回了什么状态」，
    需要更详细的信息再去 logs/shopflow.log 里看对应模块的日志。
    """
    start = time.perf_counter()
    response = await call_next(request)
    cost_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s -> %s | %.2fms",
        request.method,
        request.url.path,
        response.status_code,
        cost_ms,
    )
    return response

# 注册用户相关路由（/users/register、/users/login、/users/me）
app.include_router(users_router)
app.include_router(products_router)
app.include_router(cart_router)
app.include_router(categories_router)
app.include_router(order_router)
# 注册管理端路由（/admin/...，全部要求管理员身份，非管理员返回 403）
app.include_router(admin_router)


@app.get("/")
async def root():
    """根路径探活接口：返回服务名，用于确认后端已正常启动。"""
    return {"message": "ShopFlow Backend"}
