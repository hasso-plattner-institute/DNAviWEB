"""
One time script to create the database tables.
"""
# Run script using: python -m database.create_db
# TODO: Add Alembic for database migrations.
from database.config import engine
from database.schema.base import Base

# Pylint should not report about unused imports here as they are necessary for table
# creation in SQLAlchemy syntax.
# pylint: disable=unused-import
from database.schema import (
    biological_sex_info,
    contact_details,
    gel_electrophoresis_devices,
    hospitalization_status_enum,
    individual,
    ladder,
    ladder_peak,
    ladder_pixel,
    ontology_term,
    sample_cell_type,
    sample_disease,
    sample_phenotypic_abnormality,
    sample_pixel,
    sample_status,
    sample_treatment,
    sample_type,
    sample
    )

print("Creating DNAvi database tables.")
Base.metadata.create_all(engine)
print("DNAvi database tables created successfully!")
