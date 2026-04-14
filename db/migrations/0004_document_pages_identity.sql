BEGIN;

CREATE SCHEMA IF NOT EXISTS ops_identity;

CREATE TABLE IF NOT EXISTS ops_identity.users (
    user_id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT NULL,
    display_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    auth_subject TEXT NULL UNIQUE,
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ops_identity.roles (
    role_id TEXT PRIMARY KEY,
    role_name TEXT NOT NULL UNIQUE,
    description TEXT NULL,
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ops_identity.user_role_assignments (
    user_role_assignment_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES ops_identity.users(user_id),
    role_id TEXT NOT NULL REFERENCES ops_identity.roles(role_id),
    assigned_by TEXT NULL REFERENCES ops_identity.users(user_id),
    assigned_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, role_id)
);

CREATE TABLE IF NOT EXISTS ops_core.document_pages (
    document_page_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES ops_core.documents(document_id),
    document_version_id TEXT NOT NULL,
    page_number INTEGER NOT NULL,
    width_px INTEGER NULL,
    height_px INTEGER NULL,
    rotation_degrees NUMERIC(6,2) NOT NULL DEFAULT 0,
    preview_artifact_id TEXT NULL,
    created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (document_version_id, page_number)
);

CREATE INDEX IF NOT EXISTS idx_user_role_assignments_user_id ON ops_identity.user_role_assignments (user_id);
CREATE INDEX IF NOT EXISTS idx_document_pages_document_id ON ops_core.document_pages (document_id, page_number);

COMMIT;
