# MVP RBAC

The backend keeps access control centralized in `ops_agent.security.rbac`.

## Roles

- `ops_user`: case intake, case/document read, document upload, and document download.
- `reviewer`: ops-user access plus manual review, workflow status updates, decisions, and audit reads.
- `compliance_user`: read-only case/document access plus audit reads and compliance decision actions.
- `admin`: all MVP permissions.

## Backend Enforcement

Routes depend on permissions, not role names. Example:

```python
dependencies=[Depends(require_permission(Permission.CASE_READ))]
```

The permission map lives in `ROLE_PERMISSIONS`, so role-to-capability changes happen in one place. The MVP principal resolver reads `X-Ops-Agent-User-Id` and `X-Ops-Agent-Roles` headers and fails closed if identity is missing. A future OIDC/JWT middleware should replace only `get_current_principal`; route permission checks should remain unchanged.

## Frontend Conditional Rendering

Frontend code should not treat hidden controls as authorization. Use backend authorization as the source of truth. For UX, map the authenticated user's permissions to:

- show case creation/upload controls only with `case:create` or `document:upload`
- show correction/resubmit controls only with `manual_review:write`
- show approve/reject controls only with `decision:write`
- show audit timeline pages only with `audit:read`

When a backend request returns `403 permission_denied`, render a clear read-only or unauthorized state instead of retrying silently.
