"""
One time script to create the database tables.
"""
# Run script using: python -m database.create_db
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from database.config import engine
from database.schema.base import Base

# Pylint should not report about unused imports here as they are necessary for table
# creation in SQLAlchemy syntax.
# pylint: disable=unused-import
from database.schema import (
    biological_sex_info,
    user_details,
    gel_electrophoresis_devices,
    hospitalization_status_enum,
    ladder,
    ladder_peak,
    ladder_pixel,
    ontology_term,
    sample_pixel,
    sample,
    subject,
    submission
    )

print("Creating DNAvi database tables.")
Base.metadata.create_all(engine)
print("DNAvi database tables created successfully!")

###############################################################################
#                    INSERT DEFAULT METADATA                                  #
###############################################################################
def seed_default_values():
    """
    Seeds the database tables from the beginning with default values.
    """
    sex_rows = [
        {
            "term_label": "male",
            "term_id": "PATO:0000384",
            "ontology_description": "A biological sex quality inhering in an individual or a population whose sex organs contain only male gametes."
        },
        {
            "term_label": "female",
            "term_id": "PATO:0000383",
            "ontology_description": "A biological sex quality inhering in an individual or a population that only produces gametes that can be fertilised by male gametes."
        },
        {
            "term_label": "hermaphrodite",
            "term_id": "PATO:0001340",
            "ontology_description": "An organism having both male and female sexual characteristics and organs."
        },
        {
            "term_label": "pseudohermaphrodite",
            "term_id": "PATO:0001827",
            "ontology_description": "Having internal reproductive organs of one sex and external sexual characteristics of the other sex."
        },
        {
            "term_label": "unknown",
            "term_id": "NCIT:C17998",
            "ontology_description": "The biological sex is unknown, not assessed or not available."
        }
    ]
    
    gel_electrophoresis_devices_rows = [
        {
            "device_name": "2100 Bioanalyzer Instrument, Agilent"
        },
        {
            "device_name": "4150 TapeStation System, Agilent"
        },
        {
            "device_name": "4200 TapeStation System, Agilent"
        },
        {
            "device_name": "5200 Fragment Analyzer System, Agilent"
        },
        {
            "device_name": "5300 Fragment Analyzer System, Agilent"
        },
        {
            "device_name": "5400 Fragment Analyzer System, Agilent"
        },
        {
            "device_name": "Qsep 1 Bio-Fragment Analyzer, Nippon"
        },
        {
            "device_name": "Qsep 100 Bio-Fragment Analyzer, Nippon"
        },
        {
            "device_name": "Qsep 400 Bio-Fragment Analyzer, Nippon"
        }
    ]

    with Session(engine) as session:
        # Seed sex
        for row in sex_rows:
            stmt = (
                insert(ontology_term.OntologyTerm)
                .values(**row)
                .on_conflict_do_nothing(index_elements=["term_id"])
            )
            session.execute(stmt)
        # Seed devices
        for row in gel_electrophoresis_devices_rows:
            stmt = (
                insert(gel_electrophoresis_devices.GelElectrophoresisDevice)
                .values(**row)
                .on_conflict_do_nothing(index_elements=["device_name"])
            )
            session.execute(stmt)
        session.commit()
    print("Default ontology terms (biological sex) and gel electrophoresis devices seeded successfully!")

seed_default_values()
print("Database setup completed successfully!")