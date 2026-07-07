import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class MedicationStatus(str, Enum):
    TAKEN = "taken"
    MISSED = "missed"
    SKIPPED = "skipped"
    LATE = "late"


class MedicationLog(Base):
    __tablename__ = "medication_logs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    medication_id = Column(
        UUID(as_uuid=True),
        ForeignKey("medications.id"),
        nullable=False,
    )

    scheduled_time = Column(
        DateTime,
        nullable=False,
    )

    taken_time = Column(
        DateTime,
        nullable=True,
    )

    status = Column(
        SqlEnum(MedicationStatus),
        nullable=False,
    )

    notes = Column(Text)

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    medication = relationship(
        "Medication",
        back_populates="logs",
    )