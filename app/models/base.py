"""SQLAlchemy Base Models and Mixins.

Defines core model mixins including timestamping and serialization helpers.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, String
import uuid

from app.database import Base


def generate_uuid() -> str:
    """Generate string UUID4."""
    return str(uuid.uuid4())


class TimestampMixin:
    """Standard audit timestamps for semiconductor manufacturing records."""
    
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class FabModelBase(Base, TimestampMixin):
    """Abstract Base Model for all Fab database entities."""
    __abstract__ = True

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)

    def to_dict(self) -> dict:
        """Convert model attributes to dictionary."""
        return {
            col.name: getattr(self, col.name)
            for col in self.__table__.columns
        }
