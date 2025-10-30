"""
This module stores the sample pixels table.
"""
from sqlalchemy import Integer, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.schema.base import Base


class SamplePixel(Base):
    """
    This table stores all samples pixels from the input gel electrophoresis image.
    primary key is (sample_id, pixel_order).
    """
    __tablename__ = 'sample_pixel'
    sample_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sample.sample_id", ondelete="CASCADE"),
        primary_key=True
    )

    pixel_order: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        comment="Sequential order of the pixel in the gel image."
    )

    pixel_intensity: Mapped[float] = mapped_column(
        Numeric(30, 20),
        nullable=False,
        comment="Measured intensity of the pixel."
    )

    base_pair_position: Mapped[float] = mapped_column(
        Numeric(30, 20),
        nullable=False,
        comment="Translation of pixel intensity into fragment size (base pairs)."
    )

    # Relationships
    sample: Mapped["Sample"] = relationship(
        back_populates="sample_pixels"
    )

from database.schema.sample import Sample