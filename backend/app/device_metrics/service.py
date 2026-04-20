from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device_metrics import DeviceMetrics
from app.device_metrics.schemas import HeartbeatRequest, DeviceMetricsResponse
from app.db.influx_write import write_heartbeat
from app.events.websocket import broadcast_device_update

ONLINE_THRESHOLD_MINUTES = 5
LOW_BATTERY_THRESHOLD = 20.0


async def get_all_metrics(db: AsyncSession) -> list[DeviceMetrics]:
    result = await db.execute(
        select(DeviceMetrics).order_by(DeviceMetrics.sensor_id)
    )
    return list(result.scalars().all())


async def get_metrics_by_sensor_id(
    db: AsyncSession, sensor_id: str
) -> DeviceMetrics | None:
    result = await db.execute(
        select(DeviceMetrics).where(DeviceMetrics.sensor_id == sensor_id)
    )
    return result.scalar_one_or_none()


async def update_heartbeat(
    db: AsyncSession,
    sensor_id: str,
    location: str | None,
    heartbeat_data: HeartbeatRequest,
) -> DeviceMetrics:
    metrics = await get_metrics_by_sensor_id(db, sensor_id)

    if metrics is None:
        metrics = DeviceMetrics(
            sensor_id=sensor_id,
            location=location,
            battery_percent=heartbeat_data.battery_percent,
            bandwidth_kbps=heartbeat_data.bandwidth_kbps,
            signal_strength_dbm=heartbeat_data.signal_strength_dbm,
            firmware_version=heartbeat_data.firmware_version,
            last_heartbeat=datetime.utcnow(),
            is_online=True,
        )
        db.add(metrics)
    else:
        if location is not None:
            metrics.location = location
        if heartbeat_data.battery_percent is not None:
            metrics.battery_percent = heartbeat_data.battery_percent
        if heartbeat_data.bandwidth_kbps is not None:
            metrics.bandwidth_kbps = heartbeat_data.bandwidth_kbps
        if heartbeat_data.signal_strength_dbm is not None:
            metrics.signal_strength_dbm = heartbeat_data.signal_strength_dbm
        if heartbeat_data.firmware_version is not None:
            metrics.firmware_version = heartbeat_data.firmware_version
        metrics.last_heartbeat = datetime.utcnow()
        metrics.is_online = True

    await db.flush()
    await db.refresh(metrics)

    # Broadcast the update to all connected dashboard clients immediately
    response = DeviceMetricsResponse.model_validate(metrics)
    await broadcast_device_update(response.model_dump(mode="json"))

    # Also write to InfluxDB for time series tracking
    write_heartbeat(
        sensor_id=sensor_id,
        location=location,
        battery_percent=heartbeat_data.battery_percent,
        bandwidth_kbps=heartbeat_data.bandwidth_kbps,
        signal_strength_dbm=heartbeat_data.signal_strength_dbm,
    )

    return metrics


async def update_online_status(db: AsyncSession) -> int:
    """Mark devices as offline if no heartbeat received recently. Returns count updated."""
    threshold = datetime.utcnow() - timedelta(minutes=ONLINE_THRESHOLD_MINUTES)
    result = await db.execute(
        select(DeviceMetrics).where(
            DeviceMetrics.is_online == True,
            DeviceMetrics.last_heartbeat < threshold,
        )
    )
    stale_devices = result.scalars().all()
    for device in stale_devices:
        device.is_online = False
    await db.flush()
    return len(stale_devices)


async def get_metrics_summary(db: AsyncSession) -> dict:
    # Total devices
    total_result = await db.execute(select(func.count(DeviceMetrics.id)))
    total_devices = total_result.scalar() or 0

    # Online devices
    online_result = await db.execute(
        select(func.count(DeviceMetrics.id)).where(DeviceMetrics.is_online == True)
    )
    online_count = online_result.scalar() or 0

    # Low battery devices
    low_battery_result = await db.execute(
        select(func.count(DeviceMetrics.id)).where(
            DeviceMetrics.battery_percent < LOW_BATTERY_THRESHOLD
        )
    )
    low_battery_count = low_battery_result.scalar() or 0

    return {
        "total_devices": total_devices,
        "online_count": online_count,
        "offline_count": total_devices - online_count,
        "low_battery_count": low_battery_count,
    }
