from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FloorPlanBase(BaseModel):
    name: str
    description: str | None = None


class FloorPlanCreate(FloorPlanBase):
    pass


class FloorPlanUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class FloorPlanResponse(FloorPlanBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    width_px: int
    height_px: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class FloorPlanListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    width_px: int
    height_px: int
    is_active: bool
    created_at: datetime
