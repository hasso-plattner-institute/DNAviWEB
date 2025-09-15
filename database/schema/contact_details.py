"""
This module describes contact details of the submitter of the samples.
"""
from typing import List, Optional
from sqlalchemy import UUID, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.schema.base import Base

class ContactDetails(Base):
    """
    This table describes contact details of the submitter of the samples.
    - contact_id: Mandatory field auto generated uniquly representing the submitter.
    - email: Optional field, if the submitter would like to be able to access their data
    and be identified to request deleting data.
    - password: optional only for registered users with their email.
    - instituiton_name: Optional, Name of the institution the submitter of the data belongs to.
    """
    __tablename__ = "contact_details"

    contact_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )
    email: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    password: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    institution_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Relationship — One contact can submit many samples (one to many)
    samples: Mapped[List["Sample"]] = relationship(back_populates="contact")
