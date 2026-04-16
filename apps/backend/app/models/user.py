from __future__ import annotations

from datetime import datetime

from sqlalchemy import Enum, ForeignKey, String, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampedModel
from app.models.enums import RoleCode, UserStatus

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


class Role(TimestampedModel):
    __tablename__ = "roles"

    code: Mapped[RoleCode] = mapped_column(Enum(RoleCode, native_enum=False), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    users: Mapped[list["User"]] = relationship(secondary=user_roles, back_populates="roles")


class User(TimestampedModel):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    display_name: Mapped[str] = mapped_column(String(150))
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, native_enum=False),
        default=UserStatus.ACTIVE,
    )
    last_login_at: Mapped[datetime | None] = mapped_column(nullable=True)

    roles: Mapped[list[Role]] = relationship(secondary=user_roles, back_populates="users")
    submitted_cases: Mapped[list["Case"]] = relationship(back_populates="submitted_by_user")
    uploaded_documents: Mapped[list["Document"]] = relationship(back_populates="uploaded_by_user")

