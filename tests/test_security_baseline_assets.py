from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ops_agent.config import AppSettings
from ops_agent.security_baseline import (
    ALLOWED_UPLOAD_MIME_TYPES,
    REQUIRED_API_SECURITY_HEADERS,
    AppRole,
    ProtectedAction,
    ROLE_ACCESS_MATRIX,
)


ROOT = Path(__file__).resolve().parents[1]


def test_security_spec_exists() -> None:
    spec_path = ROOT / "docs" / "security-baseline-implementation-spec.md"
    assert spec_path.exists()


def test_close_case_excludes_basic_reviewer_role() -> None:
    assert AppRole.OPS_REVIEWER not in ROLE_ACCESS_MATRIX[ProtectedAction.CLOSE_CASE]
    assert AppRole.OPS_SUPERVISOR in ROLE_ACCESS_MATRIX[ProtectedAction.CLOSE_CASE]


def test_required_security_headers_and_upload_types_are_declared() -> None:
    assert "Strict-Transport-Security" in REQUIRED_API_SECURITY_HEADERS
    assert "application/pdf" in ALLOWED_UPLOAD_MIME_TYPES


def test_security_related_settings_have_defaults() -> None:
    settings = AppSettings.from_env()
    assert settings.oidc_audience
    assert settings.max_upload_bytes > 0
    assert settings.presigned_url_ttl_seconds > 0
