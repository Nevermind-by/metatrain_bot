from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import router as api_router
from app.api.workouts import router as workouts_router
from app.database.connection import init_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_database()
    yield


app = FastAPI(title="MetaTrain API", version="0.1.0", lifespan=lifespan)
app.include_router(api_router)
app.include_router(workouts_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
