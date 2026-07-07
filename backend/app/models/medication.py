import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class Medication(Base):
    __tablename__ = "medications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id"),
        nullable=False,
    )

    name = Column(String(100), nullable=False)

    dosage_amount = Column(Integer, nullable=False)

    dosage_unit = Column(String(20), nullable=False)

    frequency_per_day = Column(Integer, nullable=False)

    duration_days = Column(Integer, nullable=False)

    route = Column(String(50), nullable=False)

    with_food = Column(Boolean, default=False)

    empty_stomach = Column(Boolean, default=False)

    bedtime_only = Column(Boolean, default=False)

    start_date = Column(Date, nullable=False)

    end_date = Column(Date, nullable=False)

    notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="medications")

    logs = relationship(
    "MedicationLog",
    back_populates="medication",
    cascade="all, delete",
    )