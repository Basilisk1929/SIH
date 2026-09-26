"""Declarative base and common model mixins."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy 2.0 mapped models."""

    def __init__(self, **kwargs):
        if hasattr(self.__class__, "created_at") and "created_at" not in kwargs:
            kwargs["created_at"] = datetime.now(timezone.utc)
        if hasattr(self.__class__, "updated_at") and "updated_at" not in kwargs:
            kwargs["updated_at"] = datetime.now(timezone.utc)
        if hasattr(self.__class__, "is_deleted") and "is_deleted" not in kwargs:
            kwargs["is_deleted"] = False
        for k, v in kwargs.items():
            setattr(self, k, v)


class TimestampMixin:
    """Reusable mixin for creation and modification tracking."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class SoftDeleteMixin:
    """Reusable mixin for non-destructive soft deletion where appropriate."""

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def soft_delete(self) -> None:
        """Mark record as deleted with UTC timestamp."""
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        """Restore soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
