from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


from app.models.models import Base
from app.core.config import MYSQL_USER,MYSQL_PASSWORD,MYSQL_HOST,MYSQL_PORT,MYSQL_DATABASE


# 创建异步引擎
AsyncDatabaseURL = f"mysql+aiomysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
engine = create_async_engine(
    AsyncDatabaseURL,
    echo = True
)  
# 创建异步会话
AsyncSessionLocal = sessionmaker(
    engine,
    class_ = AsyncSession,
    expire_on_commit = False
)
# 数据库会话依赖（接口里写 Depends(get_session) 即可注入）
async def get_session():
    """
    每个请求分配一个 AsyncSession，请求结束后自动关闭。
    请求过程中抛异常则回滚事务，再把异常抛给上层统一处理。
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


# 建表函数
async def create_tables():
    """应用启动时按 ORM 模型元数据建表，已存在的表不会被改动。"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)




