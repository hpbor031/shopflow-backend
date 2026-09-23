from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models.models import Base

# 创建异步引擎
AsyncDatabaseURL = "mysql+aiomysql://root:just1234@localhost:3306/shopflow?charset=utf8mb4"
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
# 创建异步会话工厂
async def get_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
# 创建表函数
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)



