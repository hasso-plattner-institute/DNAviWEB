"""
This module describes all ladders.
"""
from sqlalchemy import Integer, String, ForeignKey
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

    ladder_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment=("Kind of molecular weight ladder used in  gel electrophoresis (offer"
                 "common ladder types by companies eg HSD5000, and custom option).")
    )

    gel_electrophoresis_device_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("gel_electrophoresis_devices.device_id", ondelete="CASCADE"),
        comment="Reference to the gel electrophoresis device used."
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
