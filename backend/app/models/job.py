from enum import Enum
import uuid
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import CheckConstraint
from sqlmodel import SQLModel, Field, Column, String
from pydantic import ConfigDict

class JobType(str, Enum):
    INDEXING = "indexing"
    QUERY = "query"


class JobStatus(str, Enum):
    QUEUED = "queued"
    STARTED = "started"
    DETECTING = "detecting"
    LABELLING = "labelling"
    QUERYING = "querying"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(SQLModel, table=True):
    model_config = ConfigDict(use_enum_values=True) # type: ignore
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    input_img_id: uuid.UUID = Field(foreign_key="image.id")
    input_product_id : uuid.UUID | None = Field(foreign_key="product.id")
    type: JobType = Field(
        sa_column=Column(
            String(20),
            CheckConstraint(
                # Update this constraint with new values
                f"type IN ({', '.join(repr(t.value) for t in JobType)})",
                name="check_type_enum",
            ),
            nullable=False,
        ),
    )
    status: JobStatus = Field(
        sa_column=Column(
            String(20),
            CheckConstraint(
                # Update this constraint with new values
                f"status IN ({', '.join(repr(s.value) for s in JobStatus)})",
                name="check_status_enum",
            ),
            nullable=False,
        ),
    )
    processing_details: str | None = Field(
        default=None, description="details of the current step or error."
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    update_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )

class JobPublic(SQLModel):
    id: uuid.UUID
    type: JobType
    status: JobStatus
    processing_details: str | None