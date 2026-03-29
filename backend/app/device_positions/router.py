from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.auth.dependencies import get_current_user
from app.device_positions import service
from app.device_positions.schemas import (
    DevicePositionCreate,
    DevicePositionUpdate,
    DevicePositionResponse,
    BulkPositionUpdateRequest,
)

router = APIRouter()


@router.get("", response_model=list[DevicePositionResponse])
async def list_device_positions(
    floor_plan_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    """List all device positions, optionally filtered by floor plan."""
    positions = await service.get_all_positions(db, floor_plan_id)
    return positions


@router.post("", response_model=DevicePositionResponse, status_code=201)
async def create_device_position(
    position_data: DevicePositionCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    """Create a new device position."""
    existing = await service.get_position_by_sensor_id(db, position_data.sensor_id)
    if existing is not None:
        raise HTTPException(
            status_code=400,
            detail=f"Position for sensor {position_data.sensor_id} already exists",
        )
    position = await service.create_position(db, position_data)
    return position


@router.get("/{sensor_id}", response_model=DevicePositionResponse)
async def get_device_position(
    sensor_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    """Get a device position by sensor ID."""
    position = await service.get_position_by_sensor_id(db, sensor_id)
    if position is None:
        raise HTTPException(status_code=404, detail="Device position not found")
    return position


@router.put("/{sensor_id}", response_model=DevicePositionResponse)
async def update_device_position(
    sensor_id: str,
    update_data: DevicePositionUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    """Update a device position."""
    position = await service.get_position_by_sensor_id(db, sensor_id)
    if position is None:
        raise HTTPException(status_code=404, detail="Device position not found")
    updated = await service.update_position(db, position, update_data)
    return updated


@router.delete("/{sensor_id}", status_code=204)
async def delete_device_position(
    sensor_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    """Delete a device position."""
    position = await service.get_position_by_sensor_id(db, sensor_id)
    if position is None:
        raise HTTPException(status_code=404, detail="Device position not found")
    await service.delete_position(db, position)


@router.put("/bulk", response_model=list[DevicePositionResponse])
async def bulk_update_positions(
    request: BulkPositionUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    """Bulk update device positions (for drag-and-drop)."""
    updated = await service.bulk_update_positions(db, request.positions)
    return updated
