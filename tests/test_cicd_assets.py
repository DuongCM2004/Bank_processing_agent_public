from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_cicd_build_pack_and_workflows_exist() -> None:
    assert (ROOT / "docs" / "cicd-environment-build-pack.md").exists()
    assert (ROOT / ".github" / "workflows" / "deploy.yml").exists()
    assert (ROOT / ".github" / "workflows" / "prompt-release.yml").exists()


def test_environment_layout_readme_exists() -> None:
    assert (ROOT / "infra" / "environments" / "README.md").exists()
