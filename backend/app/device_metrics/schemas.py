from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DeviceMetricsBase(BaseModel):
    sensor_id: str
    location: str | None = None
    battery_percent: float | None = None
    bandwidth_kbps: float | None = None
    signal_strength_dbm: float | None = None
    firmware_version: str | None = None


class HeartbeatRequest(BaseModel):
    battery_percent: float | None = None
    bandwidth_kbps: float | None = None
    signal_strength_dbm: float | None = None
    firmware_version: str | None = None


class DeviceMetricsResponse(DeviceMetricsBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    last_heartbeat: datetime | None
    is_online: bool
    created_at: datetime
    updated_at: datetime


class DeviceMetricsSummary(BaseModel):
    total_devices: int
    online_count: int
    offline_count: int
    low_battery_count: int
