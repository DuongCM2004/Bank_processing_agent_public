from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated

from fastapi import Depends, Header

from ops_agent.domain.shared.enums import RoleCode
from ops_agent.domain.shared.exceptions import AuthenticationRequiredError, AuthorizationError


class Permission(StrEnum):
    CASE_CREATE = "case:create"
    CASE_READ = "case:read"
    CASE_STATUS_UPDATE = "case:status:update"
    DOCUMENT_UPLOAD = "document:upload"
    DOCUMENT_READ = "document:read"
    DOCUMENT_DOWNLOAD = "document:download"
    PROCESSING_QUEUE = "processing:queue"
    MANUAL_REVIEW_WRITE = "manual_review:write"
    DECISION_WRITE = "decision:write"
    AUDIT_READ = "audit:read"
    ADMIN_MANAGE = "admin:manage"


ROLE_PERMISSIONS: dict[RoleCode, frozenset[Permission]] = {
    RoleCode.OPS_USER: frozenset(
        {
            Permission.CASE_CREATE,
            Permission.CASE_READ,
            Permission.DOCUMENT_UPLOAD,
            Permission.DOCUMENT_READ,
            Permission.DOCUMENT_DOWNLOAD,
            Permission.PROCESSING_QUEUE,
        }
    ),
    RoleCode.REVIEWER: frozenset(
        {
            Permission.CASE_CREATE,
            Permission.CASE_READ,
            Permission.CASE_STATUS_UPDATE,
            Permission.DOCUMENT_UPLOAD,
            Permission.DOCUMENT_READ,
            Permission.DOCUMENT_DOWNLOAD,
            Permission.PROCESSING_QUEUE,
            Permission.MANUAL_REVIEW_WRITE,
            Permission.DECISION_WRITE,
            Permission.AUDIT_READ,
        }
    ),
    RoleCode.COMPLIANCE_USER: frozenset(
        {
            Permission.CASE_READ,
            Permission.DOCUMENT_READ,
            Permission.DOCUMENT_DOWNLOAD,
            Permission.DECISION_WRITE,
            Permission.AUDIT_READ,
        }
    ),
    RoleCode.ADMIN: frozenset(set(Permission)),
}


@dataclass(frozen=True)
class Principal:
    subject: str
    roles: frozenset[RoleCode]
    display_name: str | None = None

    @property
    def permissions(self) -> frozenset[Permission]:
        return frozenset(permission for role in self.roles for permission in ROLE_PERMISSIONS.get(role, frozenset()))


def parse_role_codes(raw_roles: str) -> frozenset[RoleCode]:
    roles: set[RoleCode] = set()
    for raw_role in raw_roles.split(","):
        role_value = raw_role.strip()
        if not role_value:
            continue
        try:
            roles.add(RoleCode(role_value))
        except ValueError as exc:
            raise AuthorizationError(f"Unknown role '{role_value}' was supplied.") from exc

    return frozenset(roles)


def has_permission(principal: Principal, permission: Permission) -> bool:
    return permission in principal.permissions


def authorize(principal: Principal, permission: Permission) -> Principal:
    if not has_permission(principal, permission):
        raise AuthorizationError(f"Permission '{permission}' is required for this operation.")
    return principal


def get_current_principal(
    user_id: Annotated[str | None, Header(alias="X-Ops-Agent-User-Id")] = None,
    roles: Annotated[str | None, Header(alias="X-Ops-Agent-Roles")] = None,
    display_name: Annotated[str | None, Header(alias="X-Ops-Agent-Display-Name")] = None,
) -> Principal:
    """MVP principal resolver.

    This header-based resolver is a deliberate placeholder for real OIDC/session middleware.
    It fails closed when identity or roles are missing.
    """
    if not user_id or not roles:
        raise AuthenticationRequiredError()

    role_codes = parse_role_codes(roles)
    if not role_codes:
        raise AuthorizationError("At least one recognized role is required.")

    return Principal(subject=user_id, roles=role_codes, display_name=display_name)


def require_permission(permission: Permission):
    def dependency(principal: Annotated[Principal, Depends(get_current_principal)]) -> Principal:
        return authorize(principal, permission)

    return dependency
