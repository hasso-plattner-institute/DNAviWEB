"""
This module defines the ontology_term table according to its definition in the EGA metadata schema.
https://github.com/EbiEga/ega-metadata-schema/blob/main/schemas/EGA.common-definitions.json
"""
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String
from database.schema.base import Base

class OntologyTerm(Base):
    """
    EGA Definition:
    This property represents an ontology term (a.k.a. class). 
    It consists on two properties: the term identifier (termId) and its label (termLabel). 
    This property and its structure is inherited across many other elements in the 
    schemas. It is there, when inherited, where the real ontology constraint is put in place
    (e.g. using 'graphRestriction' keywords). Based on phenopacket's [OntologyClass]
    (https://phenopacket-schema.readthedocs.io/en/latest/ontologyclass.html)
    
    Columns:
    - term_id: The identifier of an ontology term must be in CURIE format (check property
    'curieGeneralPattern'). Whether a specific term is valid or not according
    to an ontology hierarchy is checked at each specific termId using ontology validation 
    keywords (e.g. 'graphRestriction').
    
    - term_label: The label of a term is the human-readable string associated with the identifier.
    It is not required that it matches the label of the termId within the referenced ontology,
    although it should. This is due to the fact that the source of truth will always be the termId,
    and not the label, which adds more context.

    - ontology_description: Optional description of the term,
    e.g., from the Ontology Lookup Service (OLS).
    Note: This field is not required by the EGA schema but added for extra clarity.
    """
    __tablename__ = "ontology_term"

    term_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    term_label: Mapped[str] = mapped_column(String(255), nullable=False)
    ontology_description: Mapped[str | None] = mapped_column(String(255), nullable=True)
