from datetime import datetime

from sqlalchemy import Integer, String, Float, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base


class DeviceMetrics(Base):
    __tablename__ = "device_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sensor_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    battery_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    bandwidth_kbps: Mapped[float | None] = mapped_column(Float, nullable=True)
    signal_strength_dbm: Mapped[float | None] = mapped_column(Float, nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_heartbeat: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_online: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
