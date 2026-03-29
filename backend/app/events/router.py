from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.service import User
from app.db.postgres import get_db
from app.device_positions import service as positions_service
from app.events.service import (
    get_events,
    get_latest_events,
    get_event_stats,
    get_loudness_timeseries,
    get_event_count_timeseries,
    get_confidence_timeseries,
    get_heatmap_data,
    get_heatmap_by_position,
    get_events_by_type_timeseries,
)
from app.events.schemas import (
    AudioEvent,
    EventStats,
    TimeSeriesPoint,
    HeatmapPoint,
    PositionalHeatmapPoint,
    EventTypeTimeSeries,
)

router = APIRouter()


@router.get("", response_model=list[AudioEvent])
async def list_events(
    time_range: str = Query("-1h", description="Time range (e.g., -1h, -24h, -7d)"),
    location: str | None = Query(None, description="Filter by location"),
    event_type: str | None = Query(None, description="Filter by event type"),
    sensor_id: str | None = Query(None, description="Filter by sensor ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of events"),
    current_user: User = Depends(get_current_user),
):
    return get_events(
        time_range=time_range,
        location=location,
        event_type=event_type,
        sensor_id=sensor_id,
        limit=limit,
    )


@router.get("/latest", response_model=list[AudioEvent])
async def list_latest_events(
    limit: int = Query(10, ge=1, le=100, description="Number of latest events"),
    current_user: User = Depends(get_current_user),
):
    return get_latest_events(limit=limit)


@router.get("/stats", response_model=EventStats)
async def get_stats(
    time_range: str = Query("-1h", description="Time range"),
    current_user: User = Depends(get_current_user),
):
    return get_event_stats(time_range=time_range)


@router.get("/timeseries/loudness", response_model=list[TimeSeriesPoint])
async def get_loudness(
    time_range: str = Query("-1h", description="Time range"),
    window: str = Query("5m", description="Aggregation window"),
    current_user: User = Depends(get_current_user),
):
    return get_loudness_timeseries(time_range=time_range, window=window)


@router.get("/timeseries/count", response_model=list[TimeSeriesPoint])
async def get_count(
    time_range: str = Query("-1h", description="Time range"),
    window: str = Query("5m", description="Aggregation window"),
    current_user: User = Depends(get_current_user),
):
    return get_event_count_timeseries(time_range=time_range, window=window)


@router.get("/timeseries/confidence", response_model=list[TimeSeriesPoint])
async def get_confidence(
    time_range: str = Query("-1h", description="Time range"),
    window: str = Query("5m", description="Aggregation window"),
    current_user: User = Depends(get_current_user),
):
    return get_confidence_timeseries(time_range=time_range, window=window)


@router.get("/heatmap", response_model=list[HeatmapPoint])
async def get_heatmap(
    time_range: str = Query("-1h", description="Time range"),
    current_user: User = Depends(get_current_user),
):
    return get_heatmap_data(time_range=time_range)


@router.get("/heatmap-by-position", response_model=list[PositionalHeatmapPoint])
async def get_heatmap_positions(
    floor_plan_id: int = Query(..., description="Floor plan ID to get positions for"),
    time_range: str = Query("-1h", description="Time range"),
    metric: str = Query("count", description="Metric: 'db', 'count', or event type name"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get heatmap data with device x/y positions for floor plan overlay."""
    positions = await positions_service.get_all_positions(db, floor_plan_id)
    position_dicts = [
        {
            "sensor_id": p.sensor_id,
            "x_coord": p.x_coord,
            "y_coord": p.y_coord,
        }
        for p in positions
    ]
    return get_heatmap_by_position(position_dicts, time_range, metric)


@router.get("/timeseries/by-type", response_model=list[EventTypeTimeSeries])
async def get_events_by_type(
    time_range: str = Query("-1h", description="Time range"),
    window: str = Query("5m", description="Aggregation window"),
    current_user: User = Depends(get_current_user),
):
    """Get time series data grouped by event type."""
    return get_events_by_type_timeseries(time_range=time_range, window=window)
