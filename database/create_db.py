"""
One time script to create the database tables.
"""
# Run script using: python -m database.create_db
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
    ladder,
    ladder_peak,
    ladder_pixel,
    ontology_term,
    sample_pixel,
    sample_type,
    sample,
    subject,
    submission
    )

print("Creating DNAvi database tables.")
Base.metadata.create_all(engine)
print("DNAvi database tables created successfully!")
