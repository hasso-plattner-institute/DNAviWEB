"""
This module defines the 'submission' table.
The submission table stores all submissions of a specific user.
"""
import uuid
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from database.schema.base import Base

class Submission(Base):
    """
    - submission_id (output_id): Each submission to DNAvi
      is identified with a unique output identifier.
    - username: username of the submitter.
    - output_files_path: Path to all output files of the submission. 
      TODO: CHANGE TO MULTIPLE FILE PATHS.
    """
    __tablename__ = 'submission'

    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    username: Mapped[str] = mapped_column(
        String(50),
        ForeignKey('user_details.username', ondelete='CASCADE'),
        nullable=False
    )

    output_files_path: Mapped[str | None] = mapped_column(
        String(255),
        nullable=False,
        comment="Path to outputs files of the submission."
    )
    
    # One user can be appear in multiple rows in the submission table
    # (One parent to Many children)
    # Parent: user
    # Child: submission
    # https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html
    user: Mapped["UserDetails"] = relationship(back_populates="submissions")

from database.schema.user_details import UserDetails