from datetime import datetime

from sqlalchemy import Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.postgres import Base


class DevicePosition(Base):
    __tablename__ = "device_positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sensor_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    floor_plan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("floor_plans.id", ondelete="CASCADE"), nullable=False
    )
    x_coord: Mapped[float] = mapped_column(Float, nullable=False)
    y_coord: Mapped[float] = mapped_column(Float, nullable=False)
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    floor_plan: Mapped["FloorPlan"] = relationship("FloorPlan", back_populates="device_positions")
