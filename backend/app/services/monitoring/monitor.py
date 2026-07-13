import asyncio
from datetime import datetime
from loguru import logger
from sqlalchemy import select, text
from app.db.database import AsyncSessionLocal
from app.models.device import Device, PingResult, Incident
from app.core.config import settings
from app.services.discovery.scanner import ping_host

async def monitor_and_alert():
    logger.info("Demarrage du monitoring automatique avec alertes")
    while True:
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(Device))
                devices = result.scalars().all()
                now = datetime.utcnow()
                for device in devices:
                    is_up, latency = await ping_host(str(device.ip_address))
                    ping_record = PingResult(
                        device_id=device.id,
                        is_up=is_up,
                        latency_ms=latency,
                        checked_at=now,
                    )
                    db.add(ping_record)
                    if not is_up and device.is_active:
                        existing = await db.execute(
                            select(Incident).where(
                                Incident.device_id == device.id,
                                Incident.status == "open"
                            )
                        )
                        if not existing.scalar_one_or_none():
                            incident = Incident(
                                device_id=device.id,
                                severity="critical",
                                title=f"Equipement hors ligne: {device.ip_address}",
                                description=f"L equipement {device.hostname or device.ip_address} ne repond plus au ping.",
                                status="open",
                            )
                            db.add(incident)
                            logger.warning(f"ALERTE: {device.ip_address} est hors ligne!")
                    elif is_up and not device.is_active:
                        existing = await db.execute(
                            select(Incident).where(
                                Incident.device_id == device.id,
                                Incident.status == "open"
                            )
                        )
                        incident = existing.scalar_one_or_none()
                        if incident:
                            incident.status = "resolved"
                            incident.resolved_at = now
                            logger.info(f"RESOLU: {device.ip_address} est de nouveau en ligne!")
                    device.is_active = is_up
                    if is_up:
                        device.last_seen = now
                await db.commit()
                logger.debug(f"Monitoring: {len(devices)} equipements verifies")
        except Exception as e:
            logger.error(f"Erreur monitoring: {e}")
        await asyncio.sleep(settings.SCAN_INTERVAL_SECONDS)
