from contextlib import asynccontextmanager

from fastapi import FastAPI

from ceresa.core.module_loader import load_enabled_modules
from ceresa.core.routes import router as system_router
from ceresa.core.settings import APP_NAME, APP_VERSION
from ceresa.db import initialize_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs application startup and shutdown tasks.

    Startup:
    - Initializes the SQLite database.
    """
    initialize_database()
    yield


app = FastAPI(
    title=APP_NAME,
    description="Centro de control local para hotel 5 estrellas.",
    version=APP_VERSION,
    lifespan=lifespan,
)


@app.get("/")
def health_check() -> dict:
    return {
        "app": APP_NAME,
        "status": "running",
        "version": APP_VERSION,
    }


app.include_router(system_router)
load_enabled_modules(app)