"""Pydantic schemas for sensor ingestion."""
from pydantic import BaseModel, Field


class DetectedEvent(BaseModel):
    """A single detected audio event."""

    label: str = Field(..., description="Event label (e.g., 'alarm', 'speech')")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score (0.0-1.0)"
    )


class IngestResponse(BaseModel):
    """Response from audio ingestion endpoint."""

    status: str = Field(..., description="Processing status ('processed' or 'error')")
    segment_id: str = Field(..., description="Unique identifier for this audio segment")
    detected_events: list[DetectedEvent] = Field(
        default_factory=list, description="List of detected events"
    )
    loudness_dba: float = Field(..., description="A-weighted audio loudness in absolute dBA")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


class IngestHealthResponse(BaseModel):
    """Response from ingestion health check endpoint."""

    model_loaded: bool = Field(..., description="Whether the ML model is loaded")
    influxdb_connected: bool = Field(..., description="Whether InfluxDB is connected")
    device: str = Field(..., description="Device used for inference (cpu/cuda)")
    num_classes: int = Field(..., description="Number of classes the model can detect")
    classes: list[str] = Field(..., description="List of class labels")
