"""
This module describes user details of the submitter of the samples.
"""
from typing import List, Optional
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import generate_password_hash, check_password_hash
from database.schema.base import Base

class UserDetails(Base):
    """
    This table describes user details of the submitter of the samples.
    - username: Mandatory field, it is the email of the submitter, if the submitter 
    would like their data saved but did not register then a random username is generated.
    - password: optional only for registered users.
    """
    __tablename__ = "user_details"

    username: Mapped[Optional[str]] = mapped_column(String(50), primary_key=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Relationship — One user can submit many times (one to many)
    submissions: Mapped[List["Submission"]] = relationship(back_populates="user")
    
    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return self.password_hash and check_password_hash(self.password_hash, password)

# This line makes sure SQLAlchemy can find the Submission class
from database.schema.submission import Submission
