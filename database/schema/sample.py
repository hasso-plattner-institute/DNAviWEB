"""
This module defines the 'sample' table.
The Sample table stores all samples and all associated metadata is either stored 
directly in the table or in additional tables that reference its primary key.
"""
from datetime import datetime
from typing import List
from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    Integer,
    String,
    ForeignKey,
    UUID,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from database.schema.in_vitro_in_vivo_enum import in_vitro_in_vivo_enum
from database.schema.mass_unit_enum import mass_unit_enum
from database.schema.volume_unit_enum import volume_unit_enum
from database.schema.base import Base
from database.schema.hospitalization_status_enum import hospitalization_status_enum

sample_status_enum = PG_ENUM(
    'case',
    'control',
    'not applicable',
    name='sample_status_enum',
    create_type=True
)

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
    
    - sample_name (in EGA objectDescription): Sample description extracted from the metadata the user typed. 
        
    - submission_id: Each submission to DNAvi is identified with a unique output identifier.

    - subject_id: Unique identifier of the subject that the sample was extracted from.

    - ladder_id: Unique identifier of the ladder used in the submission of this sample.
    
    ---------organismDescriptor-------------
    EGA: This property describes the material entity 
    the sample consists in. That is, an individual living system, such as animal, plant, bacteria 
    or virus, that is capable of replicating or reproducing, growth and maintenance in
    the right environment. An organism may be unicellular or, like humans, made
    up of many billions of cells divided into specialized tissues and organs.
    This node is of special interest in case the provenance of the sample is not
    human (e.g. microbiota taken from a donor). Unless stated otherwise, given the
    nature of the EGA, it is expected to be of human provenance.

    - organism_term_id: Taxonomic classification of the organism (e.g. 'NCBITaxon:9606' and 
     'homo sapiens' for humans) curated by the NCBI Taxonomy (search for organisms here:
      https://www.ncbi.nlm.nih.gov/taxonomy; or use the OLS: 
      https://www.ebi.ac.uk/ols/ontologies/ncbitaxon).
      You can find further details at 'https://www.uniprot.org/help/taxonomic_identifier'.
      This is appropriate for individual organisms and some environmental samples.
    - disease_term_id: https://github.com/EbiEga/ega-metadata-schema/blob/main/schemas/EGA.common-definitions.json
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
    - phenotypic_abnormality_term_id: https://github.com/EbiEga/ega-metadata-schema/blob/main/schemas/EGA.common-definitions.json
        EGA Definition:
        Property to describe any abnormal (i.e. deviation from normal or average) phenotype
        (i.e. detectable outward manifestations of a specific genotype).
        In case the phenotypic abnormality is:
        "NCIT:C17998": "Unknown",
        "NCIT:C94232": "Unaffected"
    - cell_type_term_id
    - sample_type: the material entity (e.g. DNA) that is this sample.
      Use this property as tags that befit your sample, picking as many as needed.
      Choose the specific terms if possible (e.g. if the assayed molecule is cDNA,
      add 'cDNA' instead of just 'DNA'). This property should not be confused with
      the sample collection protocols: regardless of the procedure to collect the sample,
      this property specifies what this sample is representing.
    ---------sampleCollection-------------
    Node containing the provenance details (when and where) of the sample. This information does not
    include the whole sample collection protocol (expected at experiment's protocols), only the 
    sampling date (when the sample was taken from the individual) and site (where was it taken 
    within the individual).

    - sample_collection_date: Date when the sample was collected (e.g. '2021-05-15').
    If the protocols are too long, the date shall be the day the collection concluded.

    - age_at_collection: Precise age in float format in years (20.5 years)
    EGA requires in ISO8601 format. For example, 'P3Y6M4D'
    represents a duration of three years, six months and four days.

    - sampling_site_term_id(materialAnatomicalEntity): A site or entity from which a sample
      (i.e. a statistically 
    representative of the whole) is extracted from the whole. Search for your sample collection
    site at http://purl.obolibrary.org/obo/UBERON_0000465. For example: in the case of a nasal swab,
    it would be 'nasal cavity'; in a liver biopsy it would be 'liver'.

    ---------sampleStatus-------------
    - case_vs_control
    - condition_under_study_term_id
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
    --------- sampleAttributes-------------
    - custom_sample_attributes:
    EGA Defintion: Custom attributes of a sample: reusable attributes to encode tag-value pairs
    (e.g. Tag being 'age' and its Value '30') with optional units (e.g. 'years'). Its properties are
    inherited from the common-definitions.json schema.
    ---------None EGA Metadata-------------
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
   
   - in_vitro_in_vivo: in vivo if the sample was directly extracted from a living organism, 
     otherwise if it came from a lab setup it is in vitro.

   - treatment_term_id: Medications the patient used.

   - created_at : DateTime
     Timestamp when the record was inserted.
    """

    __tablename__ = 'sample'

    sample_id: Mapped[int] = mapped_column(
      Integer,
      primary_key=True,
      autoincrement=True
    )

    sample_name: Mapped[str] = mapped_column(
      String(50),
      nullable=False
    )

    submission_id: Mapped[str] = mapped_column(
      UUID(as_uuid=True),
      ForeignKey('submission.submission_id', ondelete='CASCADE'),
      nullable=False
    )
    
    # ---------ladder table-------------
    ladder_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('ladder.ladder_id', ondelete='CASCADE'),
        nullable=False
    )

    # ---------subject table-------------
    # Unique identifier 128 bits rare to collide
    subject_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('subject.subject_id', ondelete='CASCADE'),
        nullable=True
    )
    
    # ---------Disease-------------
    disease_term_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey('ontology_term.term_id', ondelete='CASCADE'),
        nullable=True
    )
    
    # ---------Phenotypic Abnormality-------------
    phenotypic_abnormality_term_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey('ontology_term.term_id', ondelete='CASCADE'),
        nullable=True
    )

    # ---------Treatment-------------
    treatment_term_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey('ontology_term.term_id', ondelete='CASCADE'),
        nullable=True
    )

    # ---------Cell Type-------------
    cell_type_term_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey('ontology_term.term_id', ondelete='CASCADE'),
        nullable=True
    )
    
    # ---------Sample Type-------------
    sample_type: Mapped[str] = mapped_column(
        sample_type_enum,
        nullable=True
    )

    # ---------sampleCollection fields-------------
    sample_collection_date: Mapped[Date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Date when the sample was collected"
    )

    age_at_collection: Mapped[str | None] = mapped_column(
        Float,
        nullable=True
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

    # ---------sampleStatus-------------
    case_vs_control: Mapped[str] = mapped_column(
        sample_status_enum,
        nullable=True,
        comment="Whether the sample is a 'case', 'control', or 'not applicable'."
    )

    condition_under_study_term_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey('ontology_term.term_id', ondelete='CASCADE'),
        nullable=True,
        comment="Ontology term ID for the condition under study."
    )
    
    # --------- Custom Sample Attributes (sampleAttributes) -------------
    custom_sample_attributes: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment=(
            "Custom attributes of a sample: reusable attributes to encode tag-value pairs (e.g. Tag being 'age' and its Value '30') with optional units (e.g. 'years')"
        )
    )

    # ---------None EGA Metadata-------------
    # --------- sampleAttributes-------------
    #dead: PATO:0001422, alive:  PATO:0001421
    is_deceased: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True
    )

    is_pregnant: Mapped[bool | None] = mapped_column(
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

    gel_electrophoresis_device_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("gel_electrophoresis_devices.device_id", ondelete="CASCADE"),
        nullable=True,
        comment="Reference to the gel electrophoresis device used."
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(),
        nullable=False
    )

    # Relationships
    # One sample can be appear in multiple rows in the sample_treatment table (One to Many)
    # Parent: sample
    # Child: sample_treatment
    # https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html
    ladder: Mapped["Ladder"] = relationship(back_populates="samples")
    sample_pixels: Mapped[List["SamplePixel"]] = relationship(back_populates="sample")

from database.schema.ladder import Ladder
from database.schema.sample_pixel import SamplePixel
