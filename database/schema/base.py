"""
Defines the SQLAlchemy declarative base. This base class is the parent that all classes
representing tables inherit from. This way those classes can represent database tables and
interact with the database using SQLAlchemy.
"""
from sqlalchemy.orm import declarative_base

Base = declarative_base()
