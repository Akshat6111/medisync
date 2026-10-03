import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SqlEnum,
    Float,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class LabReportStatus(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class LabReportFlag(str, Enum):
    NORMAL = "normal"
    HIGH = "high"
    LOW = "low"
    UNKNOWN = "unknown"


class LabReport(Base):
    __tablename__ = "lab_reports"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    original_filename = Column(
        String(255),
        nullable=False,
    )

    uploaded_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    raw_text = Column(
        Text,
        nullable=True,
    )

    status = Column(
        SqlEnum(LabReportStatus, name="lab_report_status"),
        nullable=False,
        default=LabReportStatus.PROCESSING,
    )

    summary = Column(
        Text,
        nullable=True,
    )

    patient = relationship(
        "Patient",
        back_populates="reports",
    )

    values = relationship(
        "LabReportValue",
        back_populates="report",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class LabReportValue(Base):
    __tablename__ = "lab_report_values"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    report_id = Column(
        UUID(as_uuid=True),
        ForeignKey("lab_reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    test_name = Column(
        String(150),
        nullable=False,
    )

    value = Column(
        Float,
        nullable=False,
    )

    unit = Column(
        String(50),
        nullable=False,
    )

    reference_low = Column(
        Float,
        nullable=True,
    )

    reference_high = Column(
        Float,
        nullable=True,
    )

    flag = Column(
        SqlEnum(LabReportFlag, name="lab_report_flag"),
        nullable=False,
        default=LabReportFlag.UNKNOWN,
    )

    report = relationship(
        "LabReport",
        back_populates="values",
    )
