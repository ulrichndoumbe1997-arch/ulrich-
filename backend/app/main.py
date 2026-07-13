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
from app.db.database import init_db, AsyncSessionLocal
from app.api.routes.devices import router as devices_router
from app.api.routes.network import scanner_router, zones_router, dashboard_router
from app.services.discovery.scanner import monitor_loop


# ─── Lifespan : démarrage / arrêt ────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Démarrage de {settings.APP_NAME} v{settings.APP_VERSION}")

    # Initialiser la base de données
    await init_db()

    # Lancer la boucle de monitoring en arrière-plan
    # (désactiver en dev si pas de réseau dispo)
    monitoring_task = asyncio.create_task(
        monitor_loop(AsyncSessionLocal, "192.168.1.0/24")
        )

    asyncio.create_task(monitor_and_alert())
    yield

    # Nettoyage à l'arrêt
    monitoring_task.cancel()
    logger.info("Arrêt de l'application")


# ─── Application FastAPI ──────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## ULRICH — Outil de supervision réseau

API REST complète pour :
- 🔍 **Découverte automatique** des équipements réseau
- 📊 **Monitoring** de la disponibilité et des métriques
- 🗺️ **Topologie** graphique du réseau
- 🚨 **Alertes** en cas d'indisponibilité
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ─── CORS (accès depuis le frontend React) ───────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routes ───────────────────────────────────────────────────────────────────
app.include_router(devices_router,   prefix="/api/v1")
app.include_router(scanner_router,   prefix="/api/v1")
app.include_router(zones_router,     prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")


# ─── Endpoints de santé ───────────────────────────────────────────────────────
@app.get("/", tags=["Santé"])
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Santé"])
async def health():
    return {"status": "ok"}


# ─── Fichiers __init__.py ─────────────────────────────────────────────────────
# (créés automatiquement au démarrage via le script de setup)

import asyncio
from app.services.monitoring.monitor import monitor_and_alert
