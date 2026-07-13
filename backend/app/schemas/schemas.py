from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Any
from datetime import datetime
import uuid

class ZoneBase(BaseModel):
    name: str
    description: Optional[str] = None
    color: str = "#3B82F6"

class ZoneCreate(ZoneBase):
    pass

class ZoneOut(ZoneBase):
    id: uuid.UUID
    created_at: datetime
    model_config = {"from_attributes": True}

class DeviceBase(BaseModel):
    ip_address: str
    hostname: Optional[str] = None
    device_type: str = "unknown"
    vendor: Optional[str] = None
    os_info: Optional[str] = None
    zone_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None

    @field_validator('ip_address', mode='before')
    @classmethod
    def convert_ip(cls, v):
        return str(v)

class DeviceCreate(DeviceBase):
    mac_address: Optional[str] = None
    snmp_community: str = "public"

class DeviceUpdate(BaseModel):
    hostname: Optional[str] = None
    device_type: Optional[str] = None
    zone_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

class DeviceOut(DeviceBase):
    id: uuid.UUID
    mac_address: Optional[str] = None
    open_ports: List[Any] = []
    is_active: bool
    last_seen: datetime
    first_seen: datetime
    created_at: datetime
    is_up: Optional[bool] = None
    latency_ms: Optional[float] = None
    uptime_percent: Optional[float] = None
    zone: Optional[ZoneOut] = None

    @field_validator('ip_address', mode='before')
    @classmethod
    def convert_ip(cls, v):
        return str(v)

    model_config = {"from_attributes": True}

class PingResultOut(BaseModel):
    id: int
    device_id: uuid.UUID
    is_up: bool
    latency_ms: Optional[float] = None
    checked_at: datetime
    model_config = {"from_attributes": True}

class IncidentOut(BaseModel):
    id: uuid.UUID
    device_id: uuid.UUID
    severity: str
    title: str
    description: Optional[str] = None
    status: str
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    model_config = {"from_attributes": True}

class IncidentAck(BaseModel):
    acknowledged_by: str

class DashboardStats(BaseModel):
    total_devices: int
    devices_up: int
    devices_down: int
    uptime_percent: float
    open_incidents: int
    by_type: dict
    by_zone: dict

class ScanRequest(BaseModel):
    network: str = Field(..., example="192.168.1.0/24")
    snmp_community: str = "public"

class ScanResult(BaseModel):
    discovered: int
    updated: int
    network: str
    duration_seconds: float
