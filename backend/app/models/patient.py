import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Date,
    Float,
    Text,
    DateTime,
    Time,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(
    UUID(as_uuid=True),
    ForeignKey("users.id"),
    unique=True,
    nullable=False,
    )

    full_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(20), nullable=False)

    height_cm = Column(Float)
    weight_kg = Column(Float)
    blood_group = Column(String(5))

    allergies = Column(Text)
    medical_conditions = Column(Text)

    wake_up_time = Column(Time, nullable=False)
    breakfast_time = Column(Time, nullable=False)
    lunch_time = Column(Time, nullable=False)
    dinner_time = Column(Time, nullable=False)
    sleep_time = Column(Time, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship(
    "User",
    back_populates="patient",
    )
    
    medications = relationship(
    "Medication",
    back_populates="patient",
    cascade="all, delete"
)