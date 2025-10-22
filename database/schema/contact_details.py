"""
This module describes contact details of the submitter of the samples.
"""
from typing import List, Optional
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.schema.base import Base

class ContactDetails(Base):
    """
    This table describes contact details of the submitter of the samples.
    - username: Mandatory field, it is the email of the submitter, if the submitter 
    would like their data saved but did not register then a random username is generated.
    - password: optional only for registered users.
    """
    __tablename__ = "contact_details"

    username: Mapped[Optional[str]] = mapped_column(String(50), primary_key=True)
    password: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Relationship — One contact can submit many times (one to many)
    submissions: Mapped[List["Submission"]] = relationship(back_populates="contact")

# This line makes sure SQLAlchemy can find the Submission class
from database.schema.submission import Submission
