from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from typing import Annotated

from fastapi import Depends, Header

from app.core.exceptions import ForbiddenError
from app.models.enums import RoleCode


class Permission(StrEnum):
    CASE_CREATE = "case:create"
    CASE_READ = "case:read"
    CASE_STATUS_UPDATE = "case:status:update"
    DOCUMENT_UPLOAD = "document:upload"
    PROCESSING_QUEUE = "processing:queue"
    DECISION_CREATE = "decision:create"
    MANUAL_REVIEW_CREATE = "manual_review:create"
    AUDIT_READ = "audit:read"


ROLE_PERMISSIONS: dict[RoleCode, set[Permission]] = {
    RoleCode.OPS_USER: {
        Permission.CASE_CREATE,
        Permission.CASE_READ,
        Permission.DOCUMENT_UPLOAD,
        Permission.PROCESSING_QUEUE,
    },
    RoleCode.REVIEWER: {
        Permission.CASE_READ,
        Permission.CASE_STATUS_UPDATE,
        Permission.MANUAL_REVIEW_CREATE,
        Permission.DECISION_CREATE,
    },
    RoleCode.COMPLIANCE_USER: {
        Permission.CASE_READ,
        Permission.MANUAL_REVIEW_CREATE,
        Permission.AUDIT_READ,
    },
    RoleCode.ADMIN: set(Permission),
}


@dataclass(frozen=True, slots=True)
class CurrentUser:
    user_id: str
    roles: frozenset[RoleCode]

    @property
    def permissions(self) -> set[Permission]:
        permissions: set[Permission] = set()
        for role in self.roles:
            permissions.update(ROLE_PERMISSIONS.get(role, set()))
        return permissions


def get_current_user(
    x_user_id: str | None = Header(default=None),
    x_roles: str | None = Header(default=None),
) -> CurrentUser:
    role_values = [role.strip() for role in (x_roles or RoleCode.ADMIN.value).split(",") if role.strip()]
    roles = frozenset(RoleCode(role) for role in role_values)
    return CurrentUser(user_id=x_user_id or "system", roles=roles)


def require_permission(permission: Permission):
    def dependency(current_user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
        if permission not in current_user.permissions:
            raise ForbiddenError("Current user does not have permission for this action.")
        return current_user

    return dependency
