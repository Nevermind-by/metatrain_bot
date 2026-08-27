from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.api.router import router as api_router
from app.api.workouts import router as workouts_router
from app.database.connection import init_database

WEB_DIR = Path(__file__).resolve().parent.parent / "web"


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


@app.get("/", include_in_schema=False)
async def web_app() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")
