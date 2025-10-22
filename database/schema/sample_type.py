"""
Module describing EGA sample types table.
Multiple rows of the same sample can appear
with different samples types.
"""
from sqlalchemy import Integer, ForeignKey
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.schema.base import Base

sample_type_enum = PG_ENUM(
    "DNA",
    "RNA",
    "metabolite",
    "protein",
    "cDNA",
    "genomic DNA",
    "mitochondrial DNA",
    "messenger RNA",
    "ncRNA",
    "non polyA RNA",
    "long non polyA RNA",
    "nuclear RNA",
    "polyA RNA",
    "long polyA RNA",
    "snRNA",
    "total RNA",
    "cell culture",
    "biofilm",
    "tissue culture",
    name="sample_type_enum",
    create_type=True
)

class SampleType(Base):
    """
    Array of sample types: the material entity (e.g. DNA) that is this sample.
    Use this property as tags that befit your sample, picking as many as needed.
    Choose the specific terms if possible (e.g. if the assayed molecule is cDNA,
    add 'cDNA' instead of just 'DNA'). This property should not be confused with
    the sample collection protocols: regardless of the procedure to collect the sample,
    this property specifies what this sample is representing.
    """
    __tablename__ = 'sample_types'

    sample_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sample.sample_id", ondelete="CASCADE"),
        primary_key=True
    )

    sample_type: Mapped[str] = mapped_column(
        sample_type_enum,
        nullable=False,
        comment="Type of material in the sample (e.g., DNA, RNA, protein).",
        primary_key=True
    )

    # Relationships
    sample: Mapped["Sample"] = relationship(
        back_populates="sample_types"
    )

from database.schema.sample import Sample