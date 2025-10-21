from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .api_routes import api
from .database import engine
from .init_db import init_models
from .routes import router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    await init_models()
    yield
    await engine.dispose()


BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
app = FastAPI(title="Cookbook API", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(router)
app.include_router(api)
