"""
This module defines the 'sample_disease' table.
Each row represents a sample and one of the diseases it has. 
If a sample has multiple diseases, it will appear in multiple
rows in the table.
The table defines the 'disease' metadata according 
to its definition in the EGA metadata schema. 
https://github.com/EbiEga/ega-metadata-schema/blob/main/schemas/EGA.common-definitions.json
"""
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.schema.base import Base

class SampleDisease(Base):
    """
    EGA Definition:
    Property to describe a 'disease' (i.e. a disposition to undergo pathological processes because
    of one or more disorders). Ontology constraints for this specific termId:
    - Must satisfy any one of the following:
      * Ontology validation of 'disease' - EFO (Example: EFO:0003101)
      * Ontology validation of 'disease' - ORDO
      * Ontology validation of 'human disease or disorder' - MONDO (Example: MONDO:0100096)
    - In case the phenotypic abnormality is unknown or there is none:
      * Unknown - NCIT:C17998
      * Unaffected - NCIT:C9423
    """
    __tablename__ = 'sample_disease'

    sample_id: Mapped[int] = mapped_column(
      Integer,
      ForeignKey('sample.sample_id', ondelete='CASCADE'),
      primary_key=True
      )

    disease_term_id: Mapped[str] = mapped_column(
      String(50),
      ForeignKey('ontology_term.term_id', ondelete='CASCADE'),
      primary_key=True
      )

    # Relationships
    # One row in sample_disease table belongs to one sample
    # and one sample can appear in many rows in sample_disease table
    # One (sample row) to Many (sample_disease rows)
    # Parent: sample
    # Child: sample_disease
    # Many always has the foreign key
    sample: Mapped["Sample"] = relationship(back_populates="sample_diseases")

    # One ontology term can be appear in multiple rows in the sample_disease table
    # (One parent to Many children)
    # Parent: ontology_term
    # Child: sample_disease
    # https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html
    ontology_term: Mapped["OntologyTerm"] = relationship(back_populates="sample_diseases")
