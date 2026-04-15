from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Table, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ops_agent.domain.shared.enums import RoleCode, UserStatus
from ops_agent.infrastructure.db.base import Base
from ops_agent.infrastructure.db.models.base import BaseModel, future_info, mvp_info


user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


class Role(BaseModel):
    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint("code", name="uq_roles_code"),)

    code: Mapped[RoleCode] = mapped_column(
        Enum(RoleCode, native_enum=False),
        nullable=False,
        info=mvp_info("Stable role code used for authorization and queue access."),
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        info=mvp_info("Human-readable role name displayed in operations tooling."),
    )
    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        info=future_info("Longer role description for admin UX and policy documentation."),
    )

    users: Mapped[list["User"]] = relationship(
        secondary=user_roles,
        back_populates="roles",
    )


class User(BaseModel):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("username", name="uq_users_username"),
        UniqueConstraint("email", name="uq_users_email"),
    )

    username: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        info=mvp_info("Login or directory identifier used by operations staff."),
    )
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        info=mvp_info("Unique email address for notifications and identity mapping."),
    )
    display_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        info=mvp_info("Display name shown in review queues and audit trails."),
    )
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, native_enum=False),
        nullable=False,
        default=UserStatus.ACTIVE,
        info=mvp_info("Explicit account state for safe operational access control."),
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        info=future_info("Operational sign-in timestamp for account monitoring."),
    )

    roles: Mapped[list[Role]] = relationship(
        secondary=user_roles,
        back_populates="users",
    )
    submitted_cases: Mapped[list["Case"]] = relationship(back_populates="submitted_by_user")
    uploaded_documents: Mapped[list["Document"]] = relationship(back_populates="uploaded_by_user")
    decisions: Mapped[list["Decision"]] = relationship(back_populates="decided_by_user")
    manual_review_actions: Mapped[list["ManualReviewAction"]] = relationship(back_populates="performed_by_user")
    audit_events: Mapped[list["AuditEvent"]] = relationship(back_populates="actor_user")
