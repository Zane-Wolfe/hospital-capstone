from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.auth.dependencies import get_current_user
from app.auth.service import verify_token
from app.floor_plans import service
from app.floor_plans.schemas import (
    FloorPlanResponse,
    FloorPlanListResponse,
    FloorPlanUpdate,
)

router = APIRouter()

ALLOWED_MIME_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}


@router.get("", response_model=list[FloorPlanListResponse])
async def list_floor_plans(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    """List all floor plans."""
    floor_plans = await service.get_all_floor_plans(db)
    return floor_plans


@router.post("", response_model=FloorPlanResponse, status_code=201)
async def create_floor_plan(
    name: str = Form(...),
    description: str | None = Form(None),
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    """Upload a new floor plan with image."""
    if image.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image type. Allowed: {', '.join(ALLOWED_MIME_TYPES)}",
        )

    image_data = await image.read()
    if len(image_data) > 5 * 1024 * 1024:  # 5MB limit
        raise HTTPException(status_code=400, detail="Image too large. Max 5MB.")

    from app.floor_plans.schemas import FloorPlanCreate

    floor_plan_data = FloorPlanCreate(name=name, description=description)
    floor_plan = await service.create_floor_plan(
        db, floor_plan_data, image_data, image.content_type
    )
    return floor_plan


@router.get("/{floor_plan_id}", response_model=FloorPlanResponse)
async def get_floor_plan(
    floor_plan_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    """Get a floor plan by ID."""
    floor_plan = await service.get_floor_plan_by_id(db, floor_plan_id)
    if floor_plan is None:
        raise HTTPException(status_code=404, detail="Floor plan not found")
    return floor_plan


@router.put("/{floor_plan_id}", response_model=FloorPlanResponse)
async def update_floor_plan(
    floor_plan_id: int,
    name: str | None = Form(None),
    description: str | None = Form(None),
    is_active: bool | None = Form(None),
    image: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    """Update a floor plan."""
    floor_plan = await service.get_floor_plan_by_id(db, floor_plan_id)
    if floor_plan is None:
        raise HTTPException(status_code=404, detail="Floor plan not found")

    image_data = None
    mime_type = None
    if image is not None:
        if image.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image type. Allowed: {', '.join(ALLOWED_MIME_TYPES)}",
            )
        image_data = await image.read()
        if len(image_data) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image too large. Max 5MB.")
        mime_type = image.content_type

    update_data = FloorPlanUpdate(name=name, description=description, is_active=is_active)
    updated = await service.update_floor_plan(
        db, floor_plan, update_data, image_data, mime_type
    )
    return updated


@router.delete("/{floor_plan_id}", status_code=204)
async def delete_floor_plan(
    floor_plan_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    """Delete a floor plan."""
    floor_plan = await service.get_floor_plan_by_id(db, floor_plan_id)
    if floor_plan is None:
        raise HTTPException(status_code=404, detail="Floor plan not found")
    await service.delete_floor_plan(db, floor_plan)


@router.get("/{floor_plan_id}/image")
async def get_floor_plan_image(
    floor_plan_id: int,
    token: str | None = Query(None, description="JWT token for authentication"),
    db: AsyncSession = Depends(get_db),
):
    """Get floor plan image binary. Accepts token as query param for img src usage."""
    # Validate token from query param
    if not token:
        raise HTTPException(status_code=401, detail="Token required")

    token_data = verify_token(token)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid token")

    floor_plan = await service.get_floor_plan_by_id(db, floor_plan_id)
    if floor_plan is None:
        raise HTTPException(status_code=404, detail="Floor plan not found")
    return Response(
        content=floor_plan.image_data,
        media_type=floor_plan.image_mime_type,
    )
