"""User model representing analysts, investigators, supervisors, and administrators."""

import uuid
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.role import Role
    from backend.app.models.case import Case
    from backend.app.models.audit import AuditLog


class User(Base, TimestampMixin, SoftDeleteMixin):
    """Authenticated platform user with assigned RBAC role and profile."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    role_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="RESTRICT"),
        index=True,
        nullable=True,
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    badge_number: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    department: Mapped[str] = mapped_column(String(150), default="Cyber Crime Cell / LEA", nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), index=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)

    # Relationships
    role_rel: Mapped[Optional["Role"]] = relationship("Role", back_populates="users", lazy="joined")
    assigned_cases: Mapped[List["Case"]] = relationship(
        "Case",
        foreign_keys="[Case.assigned_to_user_id]",
        back_populates="assigned_to",
    )
    created_cases: Mapped[List["Case"]] = relationship(
        "Case",
        foreign_keys="[Case.created_by_user_id]",
        back_populates="created_by",
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship("AuditLog", back_populates="user")

    @property
    def role(self) -> str:
        """Backwards compatibility helper returning role name string."""
        if self.role_rel:
            return self.role_rel.name
        return "analyst"
