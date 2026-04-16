from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from ops_agent.domain.shared.enums import RoleCode
from ops_agent.security.rbac import Permission, Principal, get_current_principal, has_permission, parse_role_codes


def test_role_permission_mapping_keeps_access_control_centralized() -> None:
    ops_user = Principal(subject="ops-user", roles=frozenset({RoleCode.OPS_USER}))
    reviewer = Principal(subject="reviewer", roles=frozenset({RoleCode.REVIEWER}))
    compliance_user = Principal(subject="compliance", roles=frozenset({RoleCode.COMPLIANCE_USER}))
    admin = Principal(subject="admin", roles=frozenset({RoleCode.ADMIN}))

    assert has_permission(ops_user, Permission.CASE_CREATE)
    assert not has_permission(ops_user, Permission.MANUAL_REVIEW_WRITE)
    assert has_permission(reviewer, Permission.MANUAL_REVIEW_WRITE)
    assert has_permission(compliance_user, Permission.AUDIT_READ)
    assert not has_permission(compliance_user, Permission.DOCUMENT_UPLOAD)
    assert all(has_permission(admin, permission) for permission in Permission)


def test_parse_role_codes_rejects_unknown_roles() -> None:
    assert parse_role_codes("ops_user,reviewer") == frozenset({RoleCode.OPS_USER, RoleCode.REVIEWER})

    try:
        parse_role_codes("ops_user,unknown_role")
    except Exception as exc:
        assert getattr(exc, "error_code") == "permission_denied"
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("Unknown roles must be rejected.")


def test_route_rejects_missing_authentication_when_principal_is_not_overridden(test_app) -> None:
    test_app.dependency_overrides.pop(get_current_principal, None)

    with TestClient(test_app) as unauthenticated_client:
        response = unauthenticated_client.get("/api/v1/cases")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "authentication_required"


def test_route_rejects_authenticated_principal_without_required_permission(test_app) -> None:
    test_app.dependency_overrides[get_current_principal] = lambda: Principal(
        subject="ops-user",
        roles=frozenset({RoleCode.OPS_USER}),
    )

    with TestClient(test_app) as ops_client:
        response = ops_client.patch(
            f"/api/v1/cases/{uuid4()}/status",
            json={
                "target_status": "queued_for_processing",
                "actor_type": "user",
                "actor_id": str(uuid4()),
            },
        )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"


def test_route_allows_principal_with_required_permission(test_app) -> None:
    test_app.dependency_overrides[get_current_principal] = lambda: Principal(
        subject="reviewer",
        roles=frozenset({RoleCode.REVIEWER}),
    )

    with TestClient(test_app) as reviewer_client:
        response = reviewer_client.get("/api/v1/cases")

    assert response.status_code == 200
    assert response.json()["items"] == []
