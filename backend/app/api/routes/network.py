from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timedelta
from typing import List
import uuid

from app.db.database import get_db
from app.models.device import Device, PingResult, Incident
from app.models.device import Zone
from app.schemas.schemas import (
    ScanRequest, ScanResult, DashboardStats,
    ZoneOut, ZoneCreate, IncidentOut, IncidentAck
)
from app.services.discovery.scanner import scan_network

# ─── Scanner ─────────────────────────────────────────────────────────────────
scanner_router = APIRouter(prefix="/scan", tags=["Scanner réseau"])

_scan_running = False  # verrou simple anti-double scan


@scanner_router.post("/", response_model=ScanResult)
async def launch_scan(request: ScanRequest, db: AsyncSession = Depends(get_db)):
    """Lance un scan réseau complet sur la plage CIDR fournie."""
    global _scan_running
    if _scan_running:
        raise HTTPException(status_code=409, detail="Un scan est déjà en cours")

    _scan_running = True
    try:
        result = await scan_network(request.network, db, request.snmp_community)
        return ScanResult(**result)
    finally:
        _scan_running = False


@scanner_router.get("/status")
async def scan_status():
    return {"running": _scan_running}


# ─── Zones ───────────────────────────────────────────────────────────────────
zones_router = APIRouter(prefix="/zones", tags=["Zones réseau"])


@zones_router.get("/", response_model=List[ZoneOut])
async def list_zones(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Zone).order_by(Zone.name))
    return result.scalars().all()


@zones_router.post("/", response_model=ZoneOut, status_code=201)
async def create_zone(data: ZoneCreate, db: AsyncSession = Depends(get_db)):
    zone = Zone(**data.model_dump())
    db.add(zone)
    await db.commit()
    await db.refresh(zone)
    return zone


@zones_router.delete("/{zone_id}", status_code=204)
async def delete_zone(zone_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Zone).where(Zone.id == zone_id))
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(404, "Zone introuvable")
    await db.delete(zone)
    await db.commit()


# ─── Dashboard ────────────────────────────────────────────────────────────────
dashboard_router = APIRouter(prefix="/dashboard", tags=["Tableau de bord"])


@dashboard_router.get("/stats", response_model=DashboardStats)
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Statistiques globales pour le tableau de bord."""

    # Totaux
    total = (await db.execute(func.count(Device.id).select())).scalar() or 0
    up = (await db.execute(func.count(Device.id).select().where(Device.is_active == True))).scalar() or 0
    down = total - up

    # Incidents ouverts
    open_incidents = (await db.execute(
        func.count(Incident.id).select().where(Incident.status == "open")
    )).scalar() or 0

    # Répartition par type
    by_type_rows = await db.execute(
        select(Device.device_type, func.count(Device.id))
        .group_by(Device.device_type)
    )
    by_type = {row[0]: row[1] for row in by_type_rows}

    # Répartition par zone
    by_zone_rows = await db.execute(
        select(Zone.name, func.count(Device.id))
        .join(Device, Device.zone_id == Zone.id)
        .group_by(Zone.name)
    )
    by_zone = {row[0]: row[1] for row in by_zone_rows}

    return DashboardStats(
        total_devices=total,
        devices_up=up,
        devices_down=down,
        uptime_percent=round(up / total * 100, 1) if total > 0 else 0.0,
        open_incidents=open_incidents,
        by_type=by_type,
        by_zone=by_zone,
    )


@dashboard_router.get("/incidents", response_model=List[IncidentOut])
async def get_recent_incidents(
    status: str = "open",
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    query = select(Incident).order_by(desc(Incident.created_at)).limit(limit)
    if status != "all":
        query = query.where(Incident.status == status)
    result = await db.execute(query)
    return result.scalars().all()


@dashboard_router.patch("/incidents/{incident_id}/acknowledge", response_model=IncidentOut)
async def acknowledge_incident(
    incident_id: uuid.UUID,
    data: IncidentAck,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(404, "Incident introuvable")
    incident.status = "acknowledged"
    incident.acknowledged_by = data.acknowledged_by
    incident.acknowledged_at = datetime.utcnow()
    await db.commit()
    await db.refresh(incident)
    return incident


@dashboard_router.patch("/incidents/{incident_id}/resolve", response_model=IncidentOut)
async def resolve_incident(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(404, "Incident introuvable")
    incident.status = "resolved"
    incident.resolved_at = datetime.utcnow()
    await db.commit()
    await db.refresh(incident)
    return incident


@scanner_router.post("/ports/{ip}")
async def scan_device_ports(ip: str):
    from app.services.monitoring.port_check import scan_ports
    ports = await scan_ports(ip)
    return {"ip": ip, "open_ports": ports, "total": len(ports)}
