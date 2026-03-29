from datetime import datetime

from sqlalchemy import Integer, String, Text, LargeBinary, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.postgres import Base


class FloorPlan(Base):
    __tablename__ = "floor_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    image_mime_type: Mapped[str] = mapped_column(String(50), nullable=False, default="image/png")
    width_px: Mapped[int] = mapped_column(Integer, nullable=False)
    height_px: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    device_positions: Mapped[list["DevicePosition"]] = relationship(
        "DevicePosition", back_populates="floor_plan", cascade="all, delete-orphan"
    )
