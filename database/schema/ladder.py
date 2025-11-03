"""
This module describes all ladders.
"""
from datetime import datetime
from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.schema.base import Base

class Ladder(Base):
    """
    This table stores all ladders.
    primary key is ladder_id.
    """
    __tablename__ = 'ladder'

    # Start with 1 increment by 1 for each new ladder
    ladder_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    ladder_name: Mapped[str] = mapped_column(
        String(50),
        nullable=True
    )

    # Timestamp when the record was inserted.
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(),
        nullable=False
    )

    # Relationship between parent (Ladder) and child (LadderPixel) class
    # Create a python attribute ladder_pixels, one ladder (parent)
    # has many pixels (children)
    ladder_pixels: Mapped[list["LadderPixel"]] = relationship(
        back_populates="ladder"
    )
    ladder_peaks: Mapped[list["LadderPeak"]] = relationship(
        back_populates="ladder"
    )
    samples: Mapped[list["Sample"]] = relationship(
        back_populates="ladder"
    )

from database.schema.ladder_pixel import LadderPixel
from database.schema.ladder_peak import LadderPeak
from database.schema.sample import Sample