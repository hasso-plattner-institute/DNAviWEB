"""
This module defines the biological_sex_info table.
It stores biologicalSex as defined in EGA metadata schema. 
EGA Definition: biologicalSex is an organismal quality inhering in a bearer by virtue 
of the bearer's physical expression of sexual characteristics. In other words, the trait 
that determines the individual's (from which the sample derives) reproductive function: 
mainly male or female. Term chosen from a list of controlled vocabulary (CV). If you cannot 
find your term in the CV list, please create an issue at our [metadata GitHub repository]
(https://github.com/EbiEga/ega-metadata-schema/issues/new/choose) proposing its addition.
"""
from datetime import datetime
from sqlalchemy import DateTime, String, ForeignKey
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.orm import Mapped, mapped_column
from database.schema.base import Base

biological_sex_enum = PG_ENUM(
    'male',
    'female',
    'hermaphrodite',
    'pseudohermaphrodite',
    'unknown',
    name='biological_sex_enum',
    create_type=True
)

class BiologicalSexInfo(Base):
    """
    Represents the 'biological_sex_info' table.
    Columns:
    biological_sex : biological_sex_enum (Primary Key)
        An enumerated type representing the biological sex category.
        Possible values include: 'male', 'female', 'hermaphrodite',
        'pseudohermaphrodite', 'unknown'.

    term_id : String(50), ForeignKey to ontology_term.term_id
        A foreign key linking to the ontology_term table that provides the CURIE identifier 
        and detailed metadata describing the biological sex term.
    created_at : DateTime
        Timestamp when the record was inserted.
    """
    __tablename__ = 'biological_sex_info'

    biological_sex: Mapped[str] = mapped_column(
        biological_sex_enum,
        primary_key=True
    )

    biological_sex_term_id: Mapped[str] = mapped_column(
      String(50),
      ForeignKey('ontology_term.term_id', ondelete='CASCADE'),
      nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(),
        nullable=False
    )
