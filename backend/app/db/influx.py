from influxdb_client import InfluxDBClient
from influxdb_client.client.query_api import QueryApi
from influxdb_client.client.write_api import WriteApi, SYNCHRONOUS
from app.config import get_settings

_client: InfluxDBClient | None = None
_query_api: QueryApi | None = None
_write_api: WriteApi | None = None


def get_influx_client() -> InfluxDBClient:
    global _client
    if _client is None:
        settings = get_settings()
        _client = InfluxDBClient(
            url=settings.influxdb_url,
            token=settings.influxdb_token,
            org=settings.influxdb_org,
        )
    return _client


def get_query_api() -> QueryApi:
    global _query_api
    if _query_api is None:
        _query_api = get_influx_client().query_api()
    return _query_api


def get_write_api() -> WriteApi:
    """Get or create the InfluxDB write API (synchronous mode)."""
    global _write_api
    if _write_api is None:
        _write_api = get_influx_client().write_api(write_options=SYNCHRONOUS)
    return _write_api


def close_influx_client():
    global _client, _query_api, _write_api
    if _write_api is not None:
        _write_api.close()
        _write_api = None
    if _client is not None:
        _client.close()
        _client = None
        _query_api = None
