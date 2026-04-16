from __future__ import annotations

import pytest

from app.core.exceptions import ForbiddenError
from app.models.enums import RoleCode
from app.security.rbac import CurrentUser, Permission, require_permission


def test_admin_role_has_all_permissions() -> None:
    user = CurrentUser(user_id="admin", roles=frozenset({RoleCode.ADMIN}))

    assert Permission.AUDIT_READ in user.permissions
    assert Permission.DOCUMENT_UPLOAD in user.permissions


def test_permission_dependency_rejects_missing_permission() -> None:
    dependency = require_permission(Permission.AUDIT_READ)
    user = CurrentUser(user_id="ops", roles=frozenset({RoleCode.OPS_USER}))

    with pytest.raises(ForbiddenError):
        dependency(user)

