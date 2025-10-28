"""
This module defines the file table.
The table stores all result files for a specific submission.
Each file belongs to one submission.
"""
import uuid
from sqlalchemy.sql import functions
from sqlalchemy import ForeignKey, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from database.schema.base import Base

class File(Base):
    """
    Represents a single file belonging to a submission.
    - file_id: unique UUID for the file
    - submission_id: FK to Submission table
    - file_name
    - relative_path: relative path to the file on file system (vm1)
    - uploaded_at: timestamp when file was saved
    """
    __tablename__ = "file"

    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("submission.submission_id", ondelete="CASCADE"),
        nullable=False
    )

    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    relative_path: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    uploaded_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=functions.now(),
        nullable=False
    )

    submission: Mapped["Submission"] = relationship(
        "Submission",
        back_populates="files"
    )
