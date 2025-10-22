"""
This module defines the 'sample_phenotypic_abnormality' table.
Each row represents a sample and one of the phenotypic abnormalities it has. 
If a sample has multiple phenotypic abnormalities, it will appear in multiple
rows in the table.
The table defines the 'phenotypicAbnormality' metadata according 
to its definition in the EGA metadata schema. 
https://github.com/EbiEga/ega-metadata-schema/blob/main/schemas/EGA.common-definitions.json
"""
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.schema.base import Base

class SamplePhenotypicAbnormality(Base):
    """
    EGA Definition:
    Property to describe any abnormal (i.e. deviation from normal or average) phenotype
    (i.e. detectable outward manifestations of a specific genotype).
    In case the phenotypic abnormality is:
    "NCIT:C17998": "Unknown",
    "NCIT:C94232": "Unaffected"
    """
    __tablename__ = 'sample_phenotypic_abnormality'

    sample_id: Mapped[int] = mapped_column(
      Integer,
      ForeignKey('sample.sample_id', ondelete='CASCADE'),
      primary_key=True
      )

    phenotypic_abnormality_term_id: Mapped[str] = mapped_column(
      String(50),
      ForeignKey('ontology_term.term_id', ondelete='CASCADE'),
      primary_key=True
      )

    # Relationships
    # One row in sample_phenotypic_abnormality table belongs to one sample
    # and one sample can appear in many rows in sample_phenotypic_abnormality table
    # One (sample row) to Many (sample_phenotypic_abnormality rows)
    # Parent: sample
    # Child: sample_phenotypic_abnormality
    # Many always has the foreign key
    sample: Mapped["Sample"] = relationship(
        back_populates="sample_phenotypic_abnormalities"
    )

    # One ontology term can be appear in multiple rows in the 
    # sample_phenotypic_abnormality table
    # (One parent to Many children)
    # Parent: ontology_term
    # Child: sample_phenotypic_abnormality
    # https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html
    ontology_term: Mapped["OntologyTerm"] = relationship(
        back_populates="phenotypic_abnormalities"
    )

from database.schema.sample import Sample
from database.schema.ontology_term import OntologyTerm