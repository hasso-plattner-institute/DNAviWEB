"""
Database configuration: Defining how to connect to the database.
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv() # Load environmental variables from .env

DNAVI_DB_USER = os.getenv("DNAVI_DB_USER")
DNAVI_DB_PASS = os.getenv("DNAVI_DB_PASSWORD")
DNAVI_DB_HOST = os.getenv("DNAVI_DB_HOST")
DNAVI_DB_PORT = os.getenv("DNAVI_DB_PORT")
DNAVI_DB_NAME = os.getenv("DNAVI_DB_NAME")

DATABASE_URL = (
    f"postgresql+psycopg2://{DNAVI_DB_USER}:{DNAVI_DB_PASS}"
    f"@{DNAVI_DB_HOST}:{DNAVI_DB_PORT}/{DNAVI_DB_NAME}"
)

# The engine handles database communication and connection details.
# engine uses the database driver under the hood to connect to the database.
engine = create_engine(DATABASE_URL,
                       pool_pre_ping=True,
                       pool_recycle=300,
                       pool_timeout=30)
# Session handles work with python objects and when/how to send those changes to the database.
# Keeps track of all the ORM objects
SessionLocal = sessionmaker(bind=engine)
