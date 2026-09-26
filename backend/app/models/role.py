"""Role model representing RBAC privileges and access tiers."""

import uuid
from typing import Any, List
from sqlalchemy import JSON, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, SoftDeleteMixin, TimestampMixin


class Role(Base, TimestampMixin, SoftDeleteMixin):
    """Platform access role defining permissible actions and capabilities."""

    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    permissions: Mapped[List[str]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=list,
        nullable=False,
    )

    # Relationships
    users: Mapped[List["User"]] = relationship("User", back_populates="role_rel")
