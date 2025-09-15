"""
This module descirbes the sample status.
"""
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.schema.base import Base

sample_status_enum = PG_ENUM(
    'case',
    'control',
    'not applicable',
    name='sample_status_enum',
    create_type=True
)

class SampleStatus(Base):
    """
    Statuses of the sample. Used to specify the condition(s) under study **if** the diagnosis of 
    the individual is not enough to describe the status of the sample. In other words, 
    if the differenciation between affected and unaffected groups is done at the
    sample level and not at the individual level.
    This differentiation exists when the study design is of case-control
    [[EFO:0001427](http://www.ebi.ac.uk/efo/EFO_0001427)]. 
    For example, if two samples derive from an individual with 'renal cell carcinoma',
    one deriving from the affected tissue and the other from an unaffected tissue,
    this node can be used to specify whether the sample belongs to the unaffected group
    (i.e. control) or the affected one (i.e. case). On the other hand, if two samples derived
    from different probands each, one person being affected and the other unaffected
    by the condition under study, this node **is not** required. \nSame could be applied,
    for instance, for treated or untreated samples, but not for treated or untreated individuals.
    """

    __tablename__ = 'sample_status'

    sample_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('sample.sample_id', ondelete='CASCADE'),
        primary_key=True
    )

    case_vs_control: Mapped[str] = mapped_column(
        sample_status_enum,
        nullable=False,
        comment="Whether the sample is a 'case', 'control', or 'not applicable'."
    )

    condition_under_study_term_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey('ontology_term.term_id', ondelete='CASCADE'),
        nullable=False,
        comment="Ontology term ID for the condition under study."
    )

    # Relationships
    sample: Mapped["Sample"] = relationship(
        back_populates="sample_statuses"
    )
    ontology_term: Mapped["OntologyTerm"] = relationship(
        back_populates="sample_statuses"
    )
