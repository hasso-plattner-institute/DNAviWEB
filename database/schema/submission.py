"""
This module defines the 'submission' table.
The submission table stores all submissions of a specific user.
"""
from datetime import datetime
import enum
import uuid
from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from database.schema.base import Base

class DeleteStatus(enum.Enum):
    """
    Enum for tracking submission deletion request status.
    """
    NONE = "none"        # default: not requested
    PENDING = "pending"  # user requested deletion

class Submission(Base):
    """
    - submission_id (output_id): Each submission to DNAvi
      is identified with a unique output identifier.
    - username: username of the submitter.
    - delete_status: deletion request status, pending if request was sent but not approved yet,
      none if no request sent yet. If submission is deleted it will not appear at all in this table.
    - created_at : DateTime, Timestamp when the record was inserted.
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
    
    delete_status: Mapped[DeleteStatus] = mapped_column(
        Enum(DeleteStatus, name="delete_status_enum"),
        default=DeleteStatus.NONE,
        nullable=False
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(),
        nullable=False
    )
    
    # One user can be appear in multiple rows in the submission table
    # (One parent to Many children)
    # Parent: user
    # Child: submission
    # https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html
    user: Mapped["UserDetails"] = relationship(back_populates="submissions")
    files: Mapped["File"] = relationship(back_populates="submission")

from database.schema.file import File
from database.schema.user_details import UserDetails
