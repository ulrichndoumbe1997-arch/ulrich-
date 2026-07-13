import asyncio
from typing import List, Tuple

COMMON_PORTS = {
    80: "HTTP",
    443: "HTTPS", 
    22: "SSH",
    21: "FTP",
    3389: "RDP",
    8080: "HTTP-ALT",
    53: "DNS",
    25: "SMTP",
    445: "SMB",
    3306: "MySQL",
}

async def check_port(ip: str, port: int, timeout: float = 1.0) -> bool:
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port),
            timeout=timeout
        )
        writer.close()
        await writer.wait_closed()
        return True
    except Exception:
        return False

async def scan_ports(ip: str, ports: List[int] = None) -> List[dict]:
    if ports is None:
        ports = list(COMMON_PORTS.keys())
    
    tasks = [check_port(ip, port) for port in ports]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    open_ports = []
    for port, is_open in zip(ports, results):
        if is_open is True:
            open_ports.append({
                "port": port,
                "service": COMMON_PORTS.get(port, "unknown"),
                "status": "open"
            })
    
    return open_ports
