from pydantic import BaseModel
from datetime import datetime


class AudioEvent(BaseModel):
    time: datetime
    sensor_id: str
    location: str
    event_type: str
    confidence: float
    loudness_db: float


class EventStats(BaseModel):
    total_events: int
    avg_confidence: float
    avg_loudness: float
    event_types: dict[str, int]


class TimeSeriesPoint(BaseModel):
    time: datetime
    value: float


class HeatmapPoint(BaseModel):
    location: str
    count: int
    avg_loudness: float


class EventTypeTimeSeries(BaseModel):
    event_type: str
    data: list[TimeSeriesPoint]
