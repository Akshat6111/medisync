import uuid

from sqlalchemy import Column, Float, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class DrugInteraction(Base):
    __tablename__ = "drug_interactions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    drug_a = Column(
        String(100),
        nullable=False,
        index=True,
    )

    drug_b = Column(
        String(100),
        nullable=False,
        index=True,
    )

    severity = Column(
        String(20),
        nullable=False,
    )

    minimum_gap_hours = Column(
        Float,
        nullable=True,
    )

    description = Column(
        Text,
        nullable=False,
    )

    source = Column(
        String(100),
        nullable=False,
    )

    source_url = Column(
        String(500),
        nullable=True,
    )