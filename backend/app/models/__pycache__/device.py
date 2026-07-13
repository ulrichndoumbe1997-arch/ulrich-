import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, Float, BigInteger, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from app.db.database import Base

# Alias pour simplifier
TIMESTAMPTZ = DateTime(timezone=True)


class Zone(Base):
    __tablename__ = "zones"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    color: Mapped[str] = mapped_column(String(7), default="#3B82F6")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=datetime.utcnow)

    devices: Mapped[list["Device"]] = relationship("Device", back_populates="zone")


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ip_address: Mapped[str] = mapped_column(INET, unique=True, nullable=False)
    mac_address: Mapped[str | None] = mapped_column(String(17))
    hostname: Mapped[str | None] = mapped_column(String(255))
    device_type: Mapped[str] = mapped_column(String(50), default="unknown")
    vendor: Mapped[str | None] = mapped_column(String(100))
    os_info: Mapped[str | None] = mapped_column(String(200))
    zone_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("zones.id"), nullable=True)
    open_ports: Mapped[dict] = mapped_column(JSONB, default=list)
    snmp_community: Mapped[str] = mapped_column(String(100), default="public")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_seen: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=datetime.utcnow)
    first_seen: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=datetime.utcnow)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=datetime.utcnow)

    zone: Mapped["Zone | None"] = relationship("Zone", back_populates="devices")
    ping_results: Mapped[list["PingResult"]] = relationship("PingResult", back_populates="device", cascade="all, delete-orphan")
    snmp_metrics: Mapped[list["SNMPMetric"]] = relationship("SNMPMetric", back_populates="device", cascade="all, delete-orphan")
    incidents: Mapped[list["Incident"]] = relationship("Incident", back_populates="device", cascade="all, delete-orphan")


class PingResult(Base):
    __tablename__ = "ping_results"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"))
    is_up: Mapped[bool] = mapped_column(Boolean, nullable=False)
    latency_ms: Mapped[float | None] = mapped_column(Float)
    checked_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=datetime.utcnow)

    device: Mapped["Device"] = relationship("Device", back_populates="ping_results")


class SNMPMetric(Base):
    __tablename__ = "snmp_metrics"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"))
    cpu_percent: Mapped[float | None] = mapped_column(Float)
    ram_percent: Mapped[float | None] = mapped_column(Float)
    uptime_seconds: Mapped[int | None] = mapped_column(BigInteger)
    if_in_octets: Mapped[int | None] = mapped_column(BigInteger)
    if_out_octets: Mapped[int | None] = mapped_column(BigInteger)
    raw_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    collected_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=datetime.utcnow)

    device: Mapped["Device"] = relationship("Device", back_populates="snmp_metrics")


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"))
    severity: Mapped[str] = mapped_column(String(20), default="warning")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="open")
    acknowledged_by: Mapped[str | None] = mapped_column(String(100))
    acknowledged_at: Mapped[datetime | None] = mapped_column(TIMESTAMPTZ)
    resolved_at: Mapped[datetime | None] = mapped_column(TIMESTAMPTZ)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=datetime.utcnow)

    device: Mapped["Device"] = relationship("Device", back_populates="incidents")
