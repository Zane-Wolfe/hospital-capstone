from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.auth.service import User
from app.sensors.service import get_sensors, get_sensor, get_locations, Sensor

router = APIRouter()


@router.get("", response_model=list[Sensor])
async def list_sensors(
    current_user: User = Depends(get_current_user),
):
    return get_sensors()


@router.get("/locations", response_model=list[str])
async def list_locations(
    current_user: User = Depends(get_current_user),
):
    return get_locations()


@router.get("/{sensor_id}", response_model=Sensor)
async def get_sensor_by_id(
    sensor_id: str,
    current_user: User = Depends(get_current_user),
):
    sensor = get_sensor(sensor_id)
    if sensor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor {sensor_id} not found",
        )
    return sensor
