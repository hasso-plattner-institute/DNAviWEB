"""
This module describes ladder pixels.
"""
from sqlalchemy import Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.schema.base import Base

class LadderPixel(Base):
    """
    This table stores all ladder pixels from the input gel electrophoresis image.
    primary key is (ladder_id, pixel_order).
    """
    __tablename__ = 'ladder_pixel'

    ladder_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ladder.ladder_id", ondelete="CASCADE"),
        primary_key=True
    )
    pixel_order: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )
    pixel_intensity: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Pixel intensity value from the gel electrophoresis image."
    )

    # The output of DNAvi: Size in base pairs
    base_pair_position: Mapped[float] = mapped_column(
        Float,
        nullable=True,
        comment="Translation of pixel intensity into fragment size measured in base pairs."
    )

    # Create a python attribute ladder, each LadderPixel (child) belongs to one Ladder (parent)
    ladder: Mapped["Ladder"] = relationship(
        back_populates="ladder_pixels"
    )

from database.schema.ladder import Ladder
