"""
This module describes the gell ladder peaks table.
"""
from sqlalchemy import Integer, Float, ForeignKey
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

    peak_order: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        comment="Order of the peak in the ladder peak input table."
    )

    fragment_length_bp: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Fragment size in base pairs corresponding to the peak."
    )

    # Create a python attribute ladder, each LadderPeak (child) belongs to one Ladder (parent)
    ladder: Mapped["Ladder"] = relationship(
        back_populates="ladder_peaks"
    )

from database.schema.ladder import Ladder