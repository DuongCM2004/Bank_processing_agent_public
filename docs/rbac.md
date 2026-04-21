# MVP RBAC

The backend keeps access control centralized in `ops_agent.security.rbac`.

## Roles

- `ops_user`: document upload, document status read, extraction read, and artifact download where allowed.
- `reviewer`: ops-user access plus extraction table edit, approve, reject, and audit reads.
- `compliance_user`: read-only document/extraction access plus audit reads and reviewed-data approval where policy grants it.
- `admin`: all MVP permissions.

## Documents Module Permissions

The current Documents module follows [production-llm-document-extraction-backend-spec.md](D:\Self_study\computer_science\Personal_project\bank_document_processing_agent\docs\production-llm-document-extraction-backend-spec.md).

Permission checks must cover:

- `document:upload` for `POST /documents/upload`
- `document:read` for `GET /documents/{uuid}/status`
- `extraction:read` for `GET /documents/{uuid}/extraction`
- `review:write` for reviewer edits and rejects through `POST /documents/{uuid}/review`
- `review:approve` for approval through `POST /documents/{uuid}/review`
- `audit:read` for `GET /audit/{uuid}`

## Backend Enforcement

Routes depend on permissions, not role names. Example:

```python
dependencies=[Depends(require_permission(Permission.CASE_READ))]
```

The permission map lives in `ROLE_PERMISSIONS`, so role-to-capability changes happen in one place. The MVP principal resolver reads `X-Ops-Agent-User-Id` and `X-Ops-Agent-Roles` headers and fails closed if identity is missing. A future OIDC/JWT middleware should replace only `get_current_principal`; route permission checks should remain unchanged.

## Frontend Conditional Rendering

Frontend code should not treat hidden controls as authorization. Use backend authorization as the source of truth. For UX, map the authenticated user's permissions to:

- show document upload controls only with `document:upload`
- show extraction table only with `extraction:read`
- show correction/reject controls only with `review:write`
- show approve controls only with `review:approve`
- show audit timeline pages only with `audit:read`

When a backend request returns `403 permission_denied`, render a clear read-only or unauthorized state instead of retrying silently.
