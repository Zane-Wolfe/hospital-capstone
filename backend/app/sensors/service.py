from pydantic import BaseModel
from app.db.influx import get_query_api
from app.config import get_settings


class Sensor(BaseModel):
    sensor_id: str
    location: str
    last_seen: str | None = None
    event_count: int = 0


def get_sensors() -> list[Sensor]:
    settings = get_settings()
    query_api = get_query_api()

    # Query for event counts
    count_query = f'''
        from(bucket: "{settings.influxdb_bucket}")
        |> range(start: -7d)
        |> filter(fn: (r) => r["_measurement"] == "audio_events")
        |> filter(fn: (r) => r["_field"] == "confidence")
        |> group(columns: ["sensor_id", "location"])
        |> count()
    '''

    # Query for last seen timestamp
    last_seen_query = f'''
        from(bucket: "{settings.influxdb_bucket}")
        |> range(start: -7d)
        |> filter(fn: (r) => r["_measurement"] == "audio_events")
        |> filter(fn: (r) => r["_field"] == "confidence")
        |> group(columns: ["sensor_id"])
        |> last()
    '''

    count_tables = query_api.query(count_query, org=settings.influxdb_org)
    last_seen_tables = query_api.query(last_seen_query, org=settings.influxdb_org)

    # Build map of sensor_id -> last_seen
    last_seen_map: dict[str, str] = {}
    for table in last_seen_tables:
        for record in table.records:
            sensor_id = record.values.get("sensor_id", "")
            if sensor_id:
                last_seen_map[sensor_id] = record.get_time().isoformat()

    sensors_map: dict[str, Sensor] = {}

    for table in count_tables:
        for record in table.records:
            sensor_id = record.values.get("sensor_id", "")
            location = record.values.get("location", "")
            count = record.get_value() or 0

            if sensor_id not in sensors_map:
                sensors_map[sensor_id] = Sensor(
                    sensor_id=sensor_id,
                    location=location,
                    event_count=count,
                    last_seen=last_seen_map.get(sensor_id),
                )
            else:
                sensors_map[sensor_id].event_count += count

    return list(sensors_map.values())


def get_sensor(sensor_id: str) -> Sensor | None:
    sensors = get_sensors()
    for sensor in sensors:
        if sensor.sensor_id == sensor_id:
            return sensor
    return None


def get_locations() -> list[str]:
    settings = get_settings()
    query_api = get_query_api()

    query = f'''
        from(bucket: "{settings.influxdb_bucket}")
        |> range(start: -7d)
        |> filter(fn: (r) => r["_measurement"] == "audio_events")
        |> keep(columns: ["location"])
        |> distinct(column: "location")
    '''

    tables = query_api.query(query, org=settings.influxdb_org)
    locations = set()

    for table in tables:
        for record in table.records:
            location = record.values.get("location")
            if location:
                locations.add(location)

    return sorted(list(locations))
