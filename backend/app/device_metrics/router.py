from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.auth.dependencies import get_current_user
from app.ingest.tcp_auth import validate_tcp_credentials
from app.device_metrics import service
from app.device_metrics.schemas import (
    HeartbeatRequest,
    DeviceMetricsResponse,
    DeviceMetricsSummary,
)

router = APIRouter()


@router.get("", response_model=list[DeviceMetricsResponse])
async def list_device_metrics(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    """List all device metrics. Also updates online/offline status."""
    await service.update_online_status(db)
    metrics = await service.get_all_metrics(db)
    return metrics


@router.get("/summary", response_model=DeviceMetricsSummary)
async def get_metrics_summary(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    """Get summary of device metrics."""
    await service.update_online_status(db)
    summary = await service.get_metrics_summary(db)
    return summary


@router.get("/{sensor_id}", response_model=DeviceMetricsResponse)
async def get_device_metrics(
    sensor_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    """Get metrics for a specific device."""
    await service.update_online_status(db)
    metrics = await service.get_metrics_by_sensor_id(db, sensor_id)
    if metrics is None:
        raise HTTPException(status_code=404, detail="Device metrics not found")
    return metrics


@router.post("/heartbeat", response_model=DeviceMetricsResponse)
async def device_heartbeat(
    heartbeat_data: HeartbeatRequest,
    x_api_key: str = Header(..., alias="X-API-Key"),
    x_sensor_id: str = Header(..., alias="X-Sensor-ID"),
    x_location: str | None = Header(None, alias="X-Location"),
    db: AsyncSession = Depends(get_db),
):
    """ESP32 heartbeat endpoint. Uses API key auth (same as audio ingest)."""
    if not validate_tcp_credentials(x_sensor_id, x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key for sensor")

    metrics = await service.update_heartbeat(
        db, x_sensor_id, x_location, heartbeat_data
    )
    return metrics
