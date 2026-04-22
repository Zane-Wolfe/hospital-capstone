from datetime import datetime
from app.db.influx import get_query_api
from app.config import get_settings
from app.events.schemas import (
    AudioEvent,
    EventStats,
    TimeSeriesPoint,
    HeatmapPoint,
    EventTypeTimeSeries,
)


def _build_base_query(time_range: str = "-1h") -> str:
    settings = get_settings()
    return f'''
        from(bucket: "{settings.influxdb_bucket}")
        |> range(start: {time_range})
        |> filter(fn: (r) => r["_measurement"] == "audio_events")
    '''


def get_events(
    time_range: str = "-1h",
    location: str | None = None,
    event_type: str | None = None,
    sensor_id: str | None = None,
    limit: int = 100,
) -> list[AudioEvent]:
    settings = get_settings()
    query_api = get_query_api()

    filters = []
    if location:
        filters.append(f'|> filter(fn: (r) => r["location"] == "{location}")')
    if event_type:
        filters.append(f'|> filter(fn: (r) => r["event_type"] == "{event_type}")')
    if sensor_id:
        filters.append(f'|> filter(fn: (r) => r["sensor_id"] == "{sensor_id}")')

    filter_str = "\n".join(filters)

    query = f'''
        from(bucket: "{settings.influxdb_bucket}")
        |> range(start: {time_range})
        |> filter(fn: (r) => r["_measurement"] == "audio_events")
        {filter_str}
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> sort(columns: ["_time"], desc: true)
        |> limit(n: {limit})
    '''

    tables = query_api.query(query, org=settings.influxdb_org)
    events = []
    for table in tables:
        for record in table.records:
            events.append(AudioEvent(
                time=record.get_time(),
                sensor_id=record.values.get("sensor_id", ""),
                location=record.values.get("location", ""),
                event_type=record.values.get("event_type", ""),
                confidence=record.values.get("confidence", 0.0),
                loudness_dba=record.values.get("loudness_dba", 0.0),
            ))
    return events


def get_latest_events(limit: int = 10) -> list[AudioEvent]:
    return get_events(time_range="-24h", limit=limit)


def get_event_stats(time_range: str = "-1h") -> EventStats:
    settings = get_settings()
    query_api = get_query_api()

    # Count query
    count_query = f'''
        from(bucket: "{settings.influxdb_bucket}")
        |> range(start: {time_range})
        |> filter(fn: (r) => r["_measurement"] == "audio_events")
        |> filter(fn: (r) => r["_field"] == "confidence")
        |> count()
    '''

    # Average confidence query
    avg_confidence_query = f'''
        from(bucket: "{settings.influxdb_bucket}")
        |> range(start: {time_range})
        |> filter(fn: (r) => r["_measurement"] == "audio_events")
        |> filter(fn: (r) => r["_field"] == "confidence")
        |> mean()
    '''

    # Average loudness query
    avg_loudness_query = f'''
        from(bucket: "{settings.influxdb_bucket}")
        |> range(start: {time_range})
        |> filter(fn: (r) => r["_measurement"] == "audio_events")
        |> filter(fn: (r) => r["_field"] == "loudness_dba")
        |> mean()
    '''

    total_events = 0
    avg_confidence = 0.0
    avg_loudness = 0.0

    count_tables = query_api.query(count_query, org=settings.influxdb_org)
    for table in count_tables:
        for record in table.records:
            total_events = record.get_value() or 0

    confidence_tables = query_api.query(avg_confidence_query, org=settings.influxdb_org)
    for table in confidence_tables:
        for record in table.records:
            avg_confidence = record.get_value() or 0.0

    loudness_tables = query_api.query(avg_loudness_query, org=settings.influxdb_org)
    for table in loudness_tables:
        for record in table.records:
            avg_loudness = record.get_value() or 0.0

    # Event types breakdown
    events = get_events(time_range=time_range, limit=1000)
    event_types: dict[str, int] = {}
    for event in events:
        event_types[event.event_type] = event_types.get(event.event_type, 0) + 1

    return EventStats(
        total_events=total_events,
        avg_confidence=round(avg_confidence, 3),
        avg_loudness=round(avg_loudness, 2),
        event_types=event_types,
    )


def get_loudness_timeseries(time_range: str = "-1h", window: str = "5m") -> list[TimeSeriesPoint]:
    settings = get_settings()
    query_api = get_query_api()

    query = f'''
        from(bucket: "{settings.influxdb_bucket}")
        |> range(start: {time_range})
        |> filter(fn: (r) => r["_measurement"] == "audio_events")
        |> filter(fn: (r) => r["_field"] == "loudness_dba")
        |> aggregateWindow(every: {window}, fn: mean, createEmpty: false)
        |> yield(name: "mean")
    '''

    tables = query_api.query(query, org=settings.influxdb_org)
    points = []
    for table in tables:
        for record in table.records:
            points.append(TimeSeriesPoint(
                time=record.get_time(),
                value=record.get_value() or 0.0,
            ))
    return sorted(points, key=lambda p: p.time)


def get_event_count_timeseries(time_range: str = "-1h", window: str = "5m") -> list[TimeSeriesPoint]:
    settings = get_settings()
    query_api = get_query_api()

    query = f'''
        from(bucket: "{settings.influxdb_bucket}")
        |> range(start: {time_range})
        |> filter(fn: (r) => r["_measurement"] == "audio_events")
        |> filter(fn: (r) => r["_field"] == "confidence")
        |> aggregateWindow(every: {window}, fn: count, createEmpty: false)
        |> yield(name: "count")
    '''

    tables = query_api.query(query, org=settings.influxdb_org)
    points = []
    for table in tables:
        for record in table.records:
            points.append(TimeSeriesPoint(
                time=record.get_time(),
                value=float(record.get_value() or 0),
            ))
    return sorted(points, key=lambda p: p.time)


def get_confidence_timeseries(time_range: str = "-1h", window: str = "5m") -> list[TimeSeriesPoint]:
    settings = get_settings()
    query_api = get_query_api()

    query = f'''
        from(bucket: "{settings.influxdb_bucket}")
        |> range(start: {time_range})
        |> filter(fn: (r) => r["_measurement"] == "audio_events")
        |> filter(fn: (r) => r["_field"] == "confidence")
        |> aggregateWindow(every: {window}, fn: mean, createEmpty: false)
        |> yield(name: "mean")
    '''

    tables = query_api.query(query, org=settings.influxdb_org)
    points = []
    for table in tables:
        for record in table.records:
            points.append(TimeSeriesPoint(
                time=record.get_time(),
                value=record.get_value() or 0.0,
            ))
    return sorted(points, key=lambda p: p.time)


def get_heatmap_data(time_range: str = "-1h") -> list[HeatmapPoint]:
    settings = get_settings()
    query_api = get_query_api()

    # Get events grouped by location
    events = get_events(time_range=time_range, limit=10000)

    location_data: dict[str, dict] = {}
    for event in events:
        if event.location not in location_data:
            location_data[event.location] = {"count": 0, "total_loudness": 0.0}
        location_data[event.location]["count"] += 1
        location_data[event.location]["total_loudness"] += event.loudness_dba

    return [
        HeatmapPoint(
            location=loc,
            count=data["count"],
            avg_loudness=round(data["total_loudness"] / data["count"], 2) if data["count"] > 0 else 0.0,
        )
        for loc, data in location_data.items()
    ]


def get_events_by_type_timeseries(
    time_range: str = "-1h",
    window: str = "5m",
) -> list[EventTypeTimeSeries]:
    """Get time series for each event type separately."""
    settings = get_settings()
    query_api = get_query_api()

    query = f'''
        from(bucket: "{settings.influxdb_bucket}")
        |> range(start: {time_range})
        |> filter(fn: (r) => r["_measurement"] == "audio_events")
        |> filter(fn: (r) => r["_field"] == "confidence")
        |> group(columns: ["event_type"])
        |> aggregateWindow(every: {window}, fn: count, createEmpty: false)
    '''

    tables = query_api.query(query, org=settings.influxdb_org)

    # Group by event type
    event_type_data: dict[str, list[TimeSeriesPoint]] = {}
    for table in tables:
        for record in table.records:
            event_type = record.values.get("event_type", "unknown")
            if event_type not in event_type_data:
                event_type_data[event_type] = []
            event_type_data[event_type].append(
                TimeSeriesPoint(
                    time=record.get_time(),
                    value=float(record.get_value() or 0),
                )
            )

    return [
        EventTypeTimeSeries(
            event_type=et,
            data=sorted(points, key=lambda p: p.time),
        )
        for et, points in event_type_data.items()
    ]
