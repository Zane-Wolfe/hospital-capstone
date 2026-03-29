from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device_position import DevicePosition
from app.device_positions.schemas import (
    DevicePositionCreate,
    DevicePositionUpdate,
    BulkPositionUpdate,
)


async def get_all_positions(
    db: AsyncSession, floor_plan_id: int | None = None
) -> list[DevicePosition]:
    query = select(DevicePosition)
    if floor_plan_id is not None:
        query = query.where(DevicePosition.floor_plan_id == floor_plan_id)
    result = await db.execute(query.order_by(DevicePosition.sensor_id))
    return list(result.scalars().all())


async def get_position_by_sensor_id(
    db: AsyncSession, sensor_id: str
) -> DevicePosition | None:
    result = await db.execute(
        select(DevicePosition).where(DevicePosition.sensor_id == sensor_id)
    )
    return result.scalar_one_or_none()


async def create_position(
    db: AsyncSession, position_data: DevicePositionCreate
) -> DevicePosition:
    position = DevicePosition(
        sensor_id=position_data.sensor_id,
        floor_plan_id=position_data.floor_plan_id,
        x_coord=position_data.x_coord,
        y_coord=position_data.y_coord,
        label=position_data.label,
    )
    db.add(position)
    await db.flush()
    await db.refresh(position)
    return position


async def update_position(
    db: AsyncSession,
    position: DevicePosition,
    update_data: DevicePositionUpdate,
) -> DevicePosition:
    if update_data.floor_plan_id is not None:
        position.floor_plan_id = update_data.floor_plan_id
    if update_data.x_coord is not None:
        position.x_coord = update_data.x_coord
    if update_data.y_coord is not None:
        position.y_coord = update_data.y_coord
    if update_data.label is not None:
        position.label = update_data.label

    await db.flush()
    await db.refresh(position)
    return position


async def delete_position(db: AsyncSession, position: DevicePosition) -> None:
    await db.delete(position)
    await db.flush()


async def bulk_update_positions(
    db: AsyncSession, updates: list[BulkPositionUpdate]
) -> list[DevicePosition]:
    updated_positions = []
    for update in updates:
        position = await get_position_by_sensor_id(db, update.sensor_id)
        if position is not None:
            position.x_coord = update.x_coord
            position.y_coord = update.y_coord
            await db.flush()
            await db.refresh(position)
            updated_positions.append(position)
    return updated_positions
