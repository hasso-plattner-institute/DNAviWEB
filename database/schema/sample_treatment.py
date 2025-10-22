"""
This module defines the 'sample_treatment' table.
Each row represents a sample and one of the treatments it is going through,
including medications and other interventions like surgery.
If a sample has multiple treatments, it will appear in multiple
rows in the table.
"""
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.schema.base import Base

class SampleTreatment(Base):
    """
    treatment_term_id: is an ontology_term that defines the treatment that the patient
    has undergone. The terms can be looked up from OLS: https://www.ebi.ac.uk/ols4/
    Example: Ibuprofen - NCIT:C561
    """
    __tablename__ = 'sample_treatment'

    sample_id: Mapped[int] = mapped_column(
      Integer,
      ForeignKey('sample.sample_id', ondelete='CASCADE'),
      primary_key=True
      )

    treatment_term_id: Mapped[str] = mapped_column(
      String(50),
      ForeignKey('ontology_term.term_id', ondelete='CASCADE'),
      primary_key=True
      )

    # Relationships
    # One row in sample_treatment table belongs to one sample
    # and one sample can appear in many rows in sample_treatment table
    # One (sample row) to Many (sample_treatment rows)
    # Parent: sample
    # Child: sample_treatment
    # Many always has the foreign key
    sample: Mapped["Sample"] = relationship(back_populates="sample_treatments")

    # One ontology term can be appear in multiple rows in the sample_treatment table
    # (One parent to Many children)
    # Parent: ontology_term
    # Child: sample_treatment
    # https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html
    ontology_term: Mapped["OntologyTerm"] = relationship(back_populates="treatments")

from database.schema.sample import Sample
from database.schema.ontology_term import OntologyTerm