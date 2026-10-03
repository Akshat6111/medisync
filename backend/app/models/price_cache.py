import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, String
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class PriceCache(Base):
    __tablename__ = "price_cache"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    medicine_name = Column(
        String(255),
        nullable=False,
        index=True,
    )

    pharmacy_source = Column(
        String(100),
        nullable=False,
        index=True,
    )

    price = Column(
        Float,
        nullable=False,
    )

    url = Column(
        String(1000),
        nullable=True,
    )

    fetched_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )
