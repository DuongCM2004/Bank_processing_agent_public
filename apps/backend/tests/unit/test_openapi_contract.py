from __future__ import annotations


def test_openapi_exposes_domain_tags_and_common_error_schema(client) -> None:
    response = client.get("/api/v1/openapi.json")

    assert response.status_code == 200
    payload = response.json()

    tag_names = [tag["name"] for tag in payload["tags"]]
    assert tag_names == ["health", "cases", "documents", "manual-review", "decisions", "audit-events"]
    assert "ErrorEnvelope" in payload["components"]["schemas"]


def test_openapi_case_routes_use_consistent_operation_metadata(client) -> None:
    payload = client.get("/api/v1/openapi.json").json()

    list_cases = payload["paths"]["/api/v1/cases"]["get"]
    assert list_cases["operationId"] == "listCases"
    assert list_cases["tags"] == ["cases"]
    assert {"200", "422", "500"}.issubset(set(list_cases["responses"].keys()))
    assert list_cases["responses"]["422"]["content"]["application/json"]["schema"]["$ref"].endswith("/ErrorEnvelope")

    update_case_status = payload["paths"]["/api/v1/cases/{case_id}/status"]["patch"]
    assert update_case_status["operationId"] == "updateCaseStatus"
    assert {"200", "404", "409", "422", "500"}.issubset(set(update_case_status["responses"].keys()))


def test_openapi_download_route_documents_binary_and_errors(client) -> None:
    payload = client.get("/api/v1/openapi.json").json()

    download_operation = payload["paths"]["/api/v1/cases/{case_id}/documents/{document_id}/download"]["get"]
    binary_schema = download_operation["responses"]["200"]["content"]["application/octet-stream"]["schema"]

    assert download_operation["operationId"] == "downloadCaseDocument"
    assert binary_schema == {"type": "string", "format": "binary"}
    assert {"404", "409", "422", "500"}.issubset(set(download_operation["responses"].keys()))


def test_openapi_manual_review_and_audit_routes_are_frontend_friendly(client) -> None:
    payload = client.get("/api/v1/openapi.json").json()

    require_review = payload["paths"]["/api/v1/cases/{case_id}/manual-review/require"]["post"]
    audit_list = payload["paths"]["/api/v1/cases/{case_id}/audit-events"]["get"]

    assert require_review["operationId"] == "requireManualReview"
    assert require_review["summary"] == "Require manual review"
    assert require_review["tags"] == ["manual-review"]

    assert audit_list["operationId"] == "listCaseAuditEvents"
    assert audit_list["tags"] == ["audit-events"]
    parameter_names = {parameter["name"] for parameter in audit_list["parameters"]}
    assert {"case_id", "limit", "offset", "event_type", "actor_type", "resource_type"}.issubset(parameter_names)
