from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.database.database import create_tables,engine
@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield
    await engine.dispose()
app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "ShopFlow Backend"}
