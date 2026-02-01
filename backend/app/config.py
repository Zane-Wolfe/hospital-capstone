from pydantic import field_validator
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # InfluxDB
    influxdb_url: str = "http://influxdb:8086"
    influxdb_token: str
    influxdb_org: str
    influxdb_bucket: str

    # Authentication
    auth_username: str = "admin"
    auth_password: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Sensor Ingestion
    sensor_api_keys: str = ""  # Format: "sensor_001:key123,sensor_002:key456"

    # Model Configuration
    model_path: str = "/app/models/hospital_sound_classifier.pth"
    # Optional: Override confidence threshold (leave empty to use checkpoint default)
    inference_confidence_threshold: float | None = None

    # Audio Settings
    audio_sample_rate: int = 16000
    audio_segment_duration_sec: float = 1.0

    @field_validator('inference_confidence_threshold', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        if v == '':
            return None
        return v

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
