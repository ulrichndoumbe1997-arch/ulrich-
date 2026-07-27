"""
ULRICH — Network Supervision Tool
Point d'entrée principal de l'API FastAPI
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings
from app.db.database import init_db
from app.api.routes.devices import router as devices_router
from app.api.routes.network import scanner_router, zones_router, dashboard_router
from app.services.monitoring.monitor import monitor_and_alert


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Démarrage de {settings.APP_NAME} v{settings.APP_VERSION}")
    await init_db()
    asyncio.create_task(monitor_and_alert())
    yield
    logger.info("Arrêt de l'application")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="ULRICH — Outil de supervision réseau",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(devices_router,   prefix="/api/v1")
app.include_router(scanner_router,   prefix="/api/v1")
app.include_router(zones_router,     prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")


@app.get("/", tags=["Santé"])
async def root():
    return {"app": settings.APP_NAME, "version": settings.APP_VERSION, "status": "running"}


@app.get("/health", tags=["Santé"])
async def health():
    return {"status": "ok"}

from app.api.routes.auth import router as auth_router
app.include_router(auth_router, prefix="/api/v1")
