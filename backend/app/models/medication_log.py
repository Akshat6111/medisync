import uuid
from app.core.time import now_ist
from enum import Enum

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class MedicationStatus(str, Enum):
    PENDING = "pending"
    TAKEN = "taken"
    MISSED = "missed"
    SKIPPED = "skipped"
    LATE = "late"


class MedicationLog(Base):
    __tablename__ = "medication_logs"

    __table_args__ = (
        UniqueConstraint(
            "medication_id",
            "scheduled_time",
            "dose_index",
            name="uq_medication_scheduled_dose",
        ),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    medication_id = Column(
        UUID(as_uuid=True),
        ForeignKey("medications.id"),
        nullable=False,
        index=True,
    )

    dose_index = Column(
        Integer,
        nullable=False,
    )

    scheduled_time = Column(
    DateTime(timezone=True),
    nullable=False,
    )

    taken_time = Column(
    DateTime(timezone=True),
    nullable=True,
    )

    status = Column(
        SqlEnum(MedicationStatus),
        nullable=False,
        default=MedicationStatus.PENDING,
    )

    notes = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
    DateTime(timezone=True),
    default=now_ist,
    )

    medication = relationship(
        "Medication",
        back_populates="logs",
    )