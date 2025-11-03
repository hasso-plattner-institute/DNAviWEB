"""
This module defines the 'gel_electrophoresis_devices' table.
"""

from datetime import datetime
from sqlalchemy import DateTime, String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from database.schema.base import Base


class GelElectrophoresisDevice(Base):
    """
    Represents a gel electrophoresis device.

    Attributes:
        device_id (int): Primary key. Auto-incremented from 1.
        device_name (str): The name of the gel electrophoresis device.
        created_at : DateTime
        Timestamp when the record was inserted.
    """
    __tablename__ = "gel_electrophoresis_devices"

    device_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    # The name is unique to avoid storing same device multiple times.
    device_name: Mapped[str] = mapped_column(
        String(250), nullable=False, unique=True, comment="Name of the gel electrophoresis device."
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(),
        nullable=False
    )
