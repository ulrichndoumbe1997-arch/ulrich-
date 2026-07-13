from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, Integer
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from typing import List, Optional
import uuid

from app.db.database import get_db
from app.models.device import Device, PingResult, SNMPMetric, Incident
from app.schemas.schemas import DeviceOut, DeviceCreate, DeviceUpdate, PingResultOut, IncidentOut, IncidentAck
from app.services.discovery.scanner import scan_network, ping_host

router = APIRouter(prefix="/devices", tags=["Équipements"])


# ─── Liste tous les équipements ───────────────────────────────────────────────
@router.get("/", response_model=List[DeviceOut])
async def list_devices(
    zone_id: Optional[uuid.UUID] = None,
    device_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Device).options(selectinload(Device.zone))

    if zone_id:
        query = query.where(Device.zone_id == zone_id)
    if device_type:
        query = query.where(Device.device_type == device_type)
    if is_active is not None:
        query = query.where(Device.is_active == is_active)

    result = await db.execute(query.order_by(Device.ip_address))
    devices = result.scalars().all()

    # Enrichir avec le dernier ping
    enriched = []
    for device in devices:
        d = DeviceOut.model_validate(device)
        last_ping = await db.execute(
            select(PingResult)
            .where(PingResult.device_id == device.id)
            .order_by(desc(PingResult.checked_at))
            .limit(1)
        )
        ping = last_ping.scalar_one_or_none()
        if ping:
            d.is_up = ping.is_up
            d.latency_ms = ping.latency_ms

        # Calcul uptime 24h
        since = datetime.utcnow() - timedelta(hours=24)
        pings_24h = await db.execute(
            select(func.count(PingResult.id), func.sum(PingResult.is_up.cast(Integer)))
            .where(PingResult.device_id == device.id, PingResult.checked_at >= since)
        )
        total, up_count = pings_24h.one()
        if total and total > 0:
            d.uptime_percent = round((up_count or 0) / total * 100, 1)

        enriched.append(d)

    return enriched


# ─── Détail d'un équipement ───────────────────────────────────────────────────
@router.get("/{device_id}", response_model=DeviceOut)
async def get_device(device_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Device).options(selectinload(Device.zone)).where(Device.id == device_id)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Équipement introuvable")
    return device


# ─── Créer manuellement un équipement ────────────────────────────────────────
@router.post("/", response_model=DeviceOut, status_code=201)
async def create_device(data: DeviceCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Device).where(Device.ip_address == data.ip_address))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Cet équipement existe déjà")

    device = Device(**data.model_dump())
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return device


# ─── Modifier un équipement ───────────────────────────────────────────────────
@router.patch("/{device_id}", response_model=DeviceOut)
async def update_device(device_id: uuid.UUID, data: DeviceUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Équipement introuvable")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(device, field, value)
    device.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(device)
    return device


# ─── Supprimer un équipement ──────────────────────────────────────────────────
@router.delete("/{device_id}", status_code=204)
async def delete_device(device_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Équipement introuvable")
    await db.delete(device)
    await db.commit()


# ─── Ping manuel d'un équipement ─────────────────────────────────────────────
@router.post("/{device_id}/ping", response_model=PingResultOut)
async def manual_ping(device_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Équipement introuvable")

    is_up, latency = await ping_host(str(device.ip_address))
    record = PingResult(device_id=device.id, is_up=is_up, latency_ms=latency)
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


# ─── Historique de disponibilité (24h / 7j) ──────────────────────────────────
@router.get("/{device_id}/history", response_model=List[PingResultOut])
async def get_history(
    device_id: uuid.UUID,
    hours: int = 24,
    db: AsyncSession = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(hours=min(hours, 168))  # max 7 jours
    result = await db.execute(
        select(PingResult)
        .where(PingResult.device_id == device_id, PingResult.checked_at >= since)
        .order_by(desc(PingResult.checked_at))
        .limit(500)
    )
    return result.scalars().all()


# ─── Incidents d'un équipement ────────────────────────────────────────────────
@router.get("/{device_id}/incidents", response_model=List[IncidentOut])
async def get_device_incidents(device_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Incident)
        .where(Incident.device_id == device_id)
        .order_by(desc(Incident.created_at))
        .limit(50)
    )
    return result.scalars().all()
