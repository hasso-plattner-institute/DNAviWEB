"""
Different cellTypes in one sample is possible.
"""

from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.schema.base import Base

cell_type_inferred_enum = PG_ENUM(
    'inferred',
    'not inferred',
    name='cell_type_inferred_enum',
    create_type=True
)

class SampleCellType(Base):
    """
    This table includes in each row sample paird with one of the cell types it has.
    If sample includes mutliple cell types, it will have multiple rows.
    """
    # TODO backend: If they gave us the liquid type and it is in vivo default to
    # Native cell CL:0000003 (MIXED),
    # in vitro you need to specify which cell type (or unknown)
    # NCIT:C17998 (UNKNOWN).
    __tablename__ = 'sample_cell_type'

    sample_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('sample.sample_id', ondelete='CASCADE'),
        primary_key=True
    )

    cell_type_term_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey('ontology_term.term_id', ondelete='CASCADE'),
        primary_key=True
    )

    cell_type_inferred: Mapped[str] = mapped_column(
        cell_type_inferred_enum,
        nullable=True, # TODO add in frontend
        comment=("Whether the cell type is inferred ('inferred') or explicitly"
                 "known ('not inferred').")
    )

    cell_type_label: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Human-readable label for the cell type."
    )

    # Relationships
    sample: Mapped["Sample"] = relationship(
        back_populates="sample_cell_types"
    )
    ontology_term: Mapped["OntologyTerm"] = relationship(
        back_populates="cell_types"
    )
    
from database.schema.sample import Sample
from database.schema.ontology_term import OntologyTerm
