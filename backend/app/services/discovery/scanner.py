"""
Service de découverte réseau ULRICH
"""
import asyncio
import time
import socket
from datetime import datetime
from ipaddress import IPv4Network
from typing import Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.core.config import settings
from app.models.device import Device, PingResult

PORT_TYPE_MAP = {
    22: "server", 80: "server", 443: "server",
    3389: "workstation", 9100: "printer", 515: "printer",
    631: "printer", 161: "switch", 23: "router", 179: "router",
}

async def ping_host(ip: str) -> tuple[bool, Optional[float]]:
    try:
        start = time.monotonic()
        proc = await asyncio.create_subprocess_exec(
            "ping", "-c", "2", "-W", "1", ip,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5.0)
        elapsed = (time.monotonic() - start) * 1000
        if proc.returncode == 0:
            return True, round(elapsed, 2)
        return False, None
    except Exception as e:
        logger.warning(f"Ping {ip} erreur: {e}")
        return False, None


def _guess_device_type(open_ports: list, os_info: str, vendor: str) -> str:
    os_lower = os_info.lower()
    vendor_lower = vendor.lower()
    if any(v in vendor_lower for v in ["cisco", "juniper", "mikrotik", "ubiquiti"]):
        return "router"
    if any(v in vendor_lower for v in ["hp", "hewlett", "brother", "canon", "epson"]):
        return "printer"
    if "windows" in os_lower:
        return "workstation"
    if any(s in os_lower for s in ["linux", "ubuntu", "debian"]):
        return "server"
    port_numbers = [p["port"] for p in open_ports]
    for port, ptype in PORT_TYPE_MAP.items():
        if port in port_numbers:
            return ptype
    return "unknown"


async def scan_network(network_cidr: str, db: AsyncSession, snmp_community: str = "public") -> dict:
    start_time = time.monotonic()
    logger.info(f"Début du scan réseau : {network_cidr}")

    try:
        network = IPv4Network(network_cidr, strict=False)
    except ValueError as e:
        raise ValueError(f"CIDR invalide : {network_cidr} — {e}")

    ips = [str(ip) for ip in network.hosts()]
    logger.info(f"Scan de {len(ips)} adresses IP…")

    # Ping en parallèle
    active_ips = []
    batch_size = 50
    for i in range(0, len(ips), batch_size):
        batch = ips[i:i + batch_size]
        tasks = [ping_host(ip) for ip in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for ip, result in zip(batch, results):
            if isinstance(result, Exception):
                continue
            is_up, latency = result
            if is_up:
                active_ips.append((ip, latency))

    logger.info(f"Hôtes actifs détectés : {len(active_ips)}")

    discovered = 0
    updated = 0
    now = datetime.utcnow()

    for ip, latency in active_ips:
        try:
            # Recherche de l'équipement existant
            result = await db.execute(
                select(Device).where(Device.ip_address == ip)
            )
            device = result.scalar_one_or_none()

            # Essayer de résoudre le hostname
            hostname = None
            try:
                hostname = socket.gethostbyaddr(ip)[0]
            except Exception:
                pass

            if device is None:
                device = Device(
                    ip_address=ip,
                    hostname=hostname,
                    device_type="unknown",
                    is_active=True,
                    last_seen=now,
                    first_seen=now,
                    snmp_community=snmp_community,
                    open_ports=[],
                )
                db.add(device)
                await db.flush()
                discovered += 1
                logger.info(f"Nouvel équipement : {ip}")
            else:
                device.last_seen = now
                device.is_active = True
                if hostname:
                    device.hostname = hostname
                updated += 1

            ping_record = PingResult(
                device_id=device.id,
                is_up=True,
                latency_ms=latency,
                checked_at=now,
            )
            db.add(ping_record)
            await db.commit()

        except Exception as e:
            logger.error(f"Erreur traitement {ip}: {e}")
            await db.rollback()
            continue

    duration = round(time.monotonic() - start_time, 2)
    logger.info(f"Scan terminé en {duration}s — {discovered} nouveaux, {updated} mis à jour")

    return {
        "discovered": discovered,
        "updated": updated,
        "network": network_cidr,
        "duration_seconds": duration,
        "active_hosts": len(active_ips),
    }


async def monitor_loop(db_factory, network_cidr: str):
    logger.info(f"Démarrage du monitoring")
    while True:
        try:
            async with db_factory() as db:
                result = await db.execute(select(Device).where(Device.is_active == True))
                devices = result.scalars().all()
                now = datetime.utcnow()
                tasks = [ping_host(str(d.ip_address)) for d in devices]
                ping_results = await asyncio.gather(*tasks, return_exceptions=True)
                for device, ping_result in zip(devices, ping_results):
                    if isinstance(ping_result, Exception):
                        continue
                    is_up, latency = ping_result
                    record = PingResult(device_id=device.id, is_up=is_up, latency_ms=latency, checked_at=now)
                    db.add(record)
                    device.is_active = is_up
                await db.commit()
        except Exception as e:
            logger.error(f"Erreur monitor_loop: {e}")
        await asyncio.sleep(settings.SCAN_INTERVAL_SECONDS)
