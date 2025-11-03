"""
This module describes the gell ladder peaks table.
"""
from datetime import datetime
from sqlalchemy import DateTime, Integer, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.schema.base import Base

class LadderPeak(Base):
    """
    This table saves the gel ladder peaks input file.
    """
    __tablename__ = 'ladder_peak'

    ladder_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ladder.ladder_id", ondelete="CASCADE"),
        primary_key=True,
        comment="Identifier of the ladder to which this peak belongs."
    )

    peak: Mapped[str] = mapped_column(
        String(20),
        primary_key=True,
        comment="Order of the peak in the ladder peak input table: Upper_marker,1,2,...,Lower_marker"
    )

    basepairs: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Fragment size in base pairs corresponding to the peak."
    )

    # Create a python attribute ladder, each LadderPeak (child) belongs to one Ladder (parent)
    ladder: Mapped["Ladder"] = relationship(
        back_populates="ladder_peaks"
    )

    # Timestamp when the record was inserted.
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(),
        nullable=False
    )

from database.schema.ladder import Ladder