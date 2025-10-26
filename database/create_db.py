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
    sample_type,
    sample,
    subject,
    submission
    )

print("Creating DNAvi database tables.")
Base.metadata.create_all(engine)
print("DNAvi database tables created successfully!")

###############################################################################
#                    INSERT DEFAULT ONTOLOGY TERMS                            #
###############################################################################
def seed_default_ontology_terms():
    """
    Seeds the ontology_term table with default controlled vocabulary entries.
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

    with Session(engine) as session:
        for row in sex_rows:
            stmt = (
                insert(ontology_term.OntologyTerm)
                .values(**row)
                .on_conflict_do_nothing(index_elements=["term_id"])
            )
            session.execute(stmt)
        session.commit()
    print("Default ontology terms (biological sex) seeded successfully!")

seed_default_ontology_terms()
print("Database setup completed successfully!")