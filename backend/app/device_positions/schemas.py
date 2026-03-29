from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DevicePositionBase(BaseModel):
    sensor_id: str
    floor_plan_id: int
    x_coord: float
    y_coord: float
    label: str | None = None


class DevicePositionCreate(DevicePositionBase):
    pass


class DevicePositionUpdate(BaseModel):
    floor_plan_id: int | None = None
    x_coord: float | None = None
    y_coord: float | None = None
    label: str | None = None


class DevicePositionResponse(DevicePositionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class BulkPositionUpdate(BaseModel):
    sensor_id: str
    x_coord: float
    y_coord: float


class BulkPositionUpdateRequest(BaseModel):
    positions: list[BulkPositionUpdate]
