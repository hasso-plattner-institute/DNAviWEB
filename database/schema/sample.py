"""
This module defines the 'sample' table.
The Sample table stores all samples and all associated metadata is either stored 
directly in the table or in additional tables that reference its primary key.
"""
from typing import List
from sqlalchemy import (
    Boolean,
    Date,
    Float,
    Integer,
    String,
    ForeignKey,
    UUID,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.schema.in_vitro_in_vivo_enum import in_vitro_in_vivo_enum
from database.schema.mass_unit_enum import mass_unit_enum
from database.schema.volume_unit_enum import volume_unit_enum
from database.schema.base import Base
from database.schema.hospitalization_status_enum import hospitalization_status_enum


class Sample(Base):
    """    
    EGA definition: Sample metadata object is intended to contain metadata about 
    the physical sample [OBI:0000747] used in the experiment. A sample is defined as
    a limited quantity of something (e.g. a portion of a substance or individual) to be 
    used for testing, analysis, inspection, investigation, demonstration, or trial use. 
    It is a material which is collected with the intention of being representative of a
    greater whole. A sample shall not be confused with the individual (i.e. a person
    or donor) such sample derives from, for 'individual' is its own metadata object
    (https://github.com/EbiEga/ega-metadata-schema/tree/main/schemas/EGA.individual.json).
    Further details can be found in the EGA-metadata-schema GitHub repository
    (https://github.com/EbiEga/ega-metadata-schema/tree/main/schemas)
    and EGA-archive website (https://ega-archive.org/)
    
    Columns:
    
    - sample_id: Start with 1 increment by 1 for each new sample
    
    - sample_description (in EGA objectDescription): An informative sample description that
    
    describes the sample and differentiates it from others.
    
    ---------organismDescriptor-------------
    EGA: This property describes the material entity 
    the sample consists in. That is, an individual living system, such as animal, plant, bacteria 
    or virus, that is capable of replicating or reproducing, growth and maintenance in
    the right environment. An organism may be unicellular or, like humans, made
    up of many billions of cells divided into specialized tissues and organs.
    This node is of special interest in case the provenance of the sample is not
    human (e.g. microbiota taken from a donor). Unless stated otherwise, given the
    nature of the EGA, it is expected to be of human provenance.

    - organism_taxon_term_id: Taxonomic classification of the organism (e.g. 'NCBITaxon:9606' and 
    'homo sapiens' for humans) curated by the NCBI Taxonomy (search for organisms here:
    https://www.ncbi.nlm.nih.gov/taxonomy; or use the OLS: 
    https://www.ebi.ac.uk/ols/ontologies/ncbitaxon).
    You can find further details at 'https://www.uniprot.org/help/taxonomic_identifier'.
    This is appropriate for individual organisms and some environmental samples.
    
    - organism_common_name: Common name (e.g. 'human') used to designate a plant, animal or 
    other organism, as opposed to the scientific name.
    Example: "human", "goat", "horse"
    
    - subject_id: Unique identifier of the individual that the sample was extracted from.
    
    ---------sampleCollection-------------
    Node containing the provenance details (when and where) of the sample. This information does not
    include the whole sample collection protocol (expected at experiment's protocols), only the 
    sampling date (when the sample was taken from the individual) and site (where was it taken 
    within the individual).

    - sample_collection_date: Date when the sample was collected (e.g. '2021-05-15').
    If the protocols are too long, the date shall be the day the collection concluded.

    - age_at_collection: Precise age in ISO8601 format of the individual. For example, 'P3Y6M4D'
    represents a duration of three years, six months and four days.

    - sampling_site_term_id: A site or entity from which a sample (i.e. a statistically 
    representative of the whole) is extracted from the whole. Search for your sample collection
    site at http://purl.obolibrary.org/obo/UBERON_0000465. For example: in the case of a nasal swab,
    it would be 'nasal cavity'; in a liver biopsy it would be 'liver'.
    
    # ---------submission table-------------
    - contact_id: Reference to the contact who submitted the sample
    
    # ---------None EGA Metadata-------------
    # --------- sampleAttributes-------------
    EGA Defintion: Custom attributes of a sample: reusable attributes to encode tag-value pairs
    (e.g. Tag being 'age' and its Value '30') with optional units (e.g. 'years'). Its properties are
    inherited from the common-definitions.json schema.
    
    - is_deceased: 'True' if sample was collected from a deceased individual, else 'False'.
    
    - is_infection_suspected: 'True' if a sepsis or a bacterial infection is suspected, otherwise
    'False'.
    
    - infection_strain: Specify the strain involved if infection is suspected.
    
    - is_pregnant: 'True' if sample was collected from a pregnant individual, else 'False'.
    
    - hospitalization_status: Describes the hospitaloization status of the individual when the
    sample was collected according to hospitalization_status_enum.
    
    - extraction_kit: Extraction kit used.
    
   - dna_mass: Mass of DNA/RNA in the sample.
   
   - dna_mass_units: Units for DNA mass ('pg', 'ng', 'µg').
   
   - carrying_liquid_volume: Volume of DNA carrying liquid (numeric).
   
   - carrying_liquid_volume_unit: Unit of DNA carrying liquid (µL, mL, L).
    """

    __tablename__ = 'sample'

    sample_id: Mapped[int] = mapped_column(
      Integer,
      primary_key=True,
      autoincrement=True
    )

    # objectDescription
    sample_description: Mapped[int] = mapped_column(
      String(255),
      nullable=True
    )

    # ---------ladder table-------------
    ladder_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('ladder.ladder_id', ondelete='CASCADE'),
        nullable=False
    )

    # ---------organismDescriptor fields-------------
    # organismDescriptor.organismTaxon
    organism_taxon_term_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey('ontology_term.term_id', ondelete='CASCADE')
    )

    # organismDescriptor.commonName
    organism_common_name: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    # ---------individual -------------
    # Unique identifier 128 bits rare to collide
    individual_object_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('individual.individual_object_id', ondelete='CASCADE'),
        nullable=False
    )

    # ---------sampleCollection fields-------------
    sample_collection_date: Mapped[Date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Date when the sample was collected"
    )

    age_at_collection: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment=(
            "Precise age in ISO8601 format of the individual. For example, 'P3Y6M4D'"
            "represents a duration of three years, six months and four days."
        )
    )

    # Sampling site (materialAnatomicalEntity) using UBERON
    sampling_site_term_id: Mapped[str | None] = mapped_column(
        String(50),
        ForeignKey('ontology_term.term_id', ondelete='CASCADE'),
        nullable=True,
        comment=(
            "UBERON term representing the site where the sample was collected"
            "(e.g., 'nasal cavity', 'liver')"
        )
    )

    # ---------contact details-------------
    contact_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('contact_details.contact_id', ondelete='CASCADE'),
        nullable=False,
        comment="Reference to the contact who submitted the sample"
    )

    # ---------None EGA Metadata-------------
    # --------- sampleAttributes-------------
    #dead: PATO:0001422, alive:  PATO:0001421
    is_deceased: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True
    )

    is_infection_suspected: Mapped[str | None]= mapped_column(
        Boolean,
        nullable=True,
        comment= "Is True if a sepsis or a bacterial infection is suspected, otherwise False."
    )

    infection_strain: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Specify the strain involved if infection is suspected."
    )

    is_pregnant: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True
    )

    hospitalization_status: Mapped[str | None] = mapped_column(
        hospitalization_status_enum,
        nullable=True,
        comment="Status of hospitalization for the individual."
    )

    extraction_kit: Mapped[str | None] =  mapped_column(
        String(50),
        nullable=True,
        comment="Extraction kit used."
    )

    dna_mass: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="DNA amount numeric value."
    )

    # Mass units
    dna_mass_units: Mapped[str | None] = mapped_column(
        mass_unit_enum,
        nullable=True,
        comment="Units for DNA mass (e.g., 'pg', 'ng', 'µg')."
    )

    # Volume of liquid carrying the DNA/RNA
    carrying_liquid_volume: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Volume of DNA carrying liquid (numeric)."
    )

    # Carrying liquid volume units
    carrying_liquid_volume_unit: Mapped[str | None] = mapped_column(
        volume_unit_enum,
        nullable=True,
        comment="Unit of DNA carrying liquid (e.g., µL, mL, L)."
    )

    in_vitro_in_vivo: Mapped[str | None] = mapped_column(
        in_vitro_in_vivo_enum,
        nullable=True,
        comment="Indicates whether the sample originated from an in vitro or in vivo source."
    )

    gel_image_path: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Path to gel electrophoresis image file of the sample."
    )

    device_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("gel_electrophoresis_devices.device_id"),
        nullable=True,
        comment="ID of the gel electrophoresis device used for this sample."
    )

    # Relationships
    # One sample can be appear in multiple rows in the sample_treatment table (One to Many)
    # Parent: sample
    # Child: sample_treatment
    # https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html
    sample_treatments: Mapped[List["SampleTreatment"]] = relationship(back_populates="sample")
    sample_pixels: Mapped[List["SamplePixel"]] = relationship(back_populates="sample")
    sample_statuses: Mapped[List["SampleStatus"]] = relationship(back_populates="sample")
    sample_cell_types: Mapped[List["SampleCellType"]] = relationship(back_populates="sample")
    sample_types: Mapped[List["SampleType"]] = relationship(back_populates="sample")
    # One contact can be appear in multiple rows in the sample table
    # (One parent to Many children)
    # Parent: contact
    # Child: sample
    # https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html
    contact: Mapped["ContactDetails"] = relationship(back_populates="samples")
