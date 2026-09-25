from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.database import create_tables,engine
from app.api.users import router as users_router
@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield
    await engine.dispose()
app = FastAPI(lifespan=lifespan)

app.include_router(users_router)

@app.get("/")
async def root():
    return {"message": "ShopFlow Backend"}
