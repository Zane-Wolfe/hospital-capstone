from io import BytesIO
from PIL import Image

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.floor_plan import FloorPlan
from app.floor_plans.schemas import FloorPlanCreate, FloorPlanUpdate


async def get_all_floor_plans(db: AsyncSession) -> list[FloorPlan]:
    result = await db.execute(select(FloorPlan).order_by(FloorPlan.created_at.desc()))
    return list(result.scalars().all())


async def get_floor_plan_by_id(db: AsyncSession, floor_plan_id: int) -> FloorPlan | None:
    result = await db.execute(select(FloorPlan).where(FloorPlan.id == floor_plan_id))
    return result.scalar_one_or_none()


async def create_floor_plan(
    db: AsyncSession,
    floor_plan_data: FloorPlanCreate,
    image_data: bytes,
    mime_type: str,
) -> FloorPlan:
    # Get image dimensions
    img = Image.open(BytesIO(image_data))
    width, height = img.size

    floor_plan = FloorPlan(
        name=floor_plan_data.name,
        description=floor_plan_data.description,
        image_data=image_data,
        image_mime_type=mime_type,
        width_px=width,
        height_px=height,
    )
    db.add(floor_plan)
    await db.flush()
    await db.refresh(floor_plan)
    return floor_plan


async def update_floor_plan(
    db: AsyncSession,
    floor_plan: FloorPlan,
    update_data: FloorPlanUpdate,
    image_data: bytes | None = None,
    mime_type: str | None = None,
) -> FloorPlan:
    if update_data.name is not None:
        floor_plan.name = update_data.name
    if update_data.description is not None:
        floor_plan.description = update_data.description
    if update_data.is_active is not None:
        floor_plan.is_active = update_data.is_active

    if image_data is not None and mime_type is not None:
        img = Image.open(BytesIO(image_data))
        width, height = img.size
        floor_plan.image_data = image_data
        floor_plan.image_mime_type = mime_type
        floor_plan.width_px = width
        floor_plan.height_px = height

    await db.flush()
    await db.refresh(floor_plan)
    return floor_plan


async def delete_floor_plan(db: AsyncSession, floor_plan: FloorPlan) -> None:
    await db.delete(floor_plan)
    await db.flush()
