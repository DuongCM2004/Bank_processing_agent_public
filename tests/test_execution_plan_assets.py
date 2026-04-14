from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_engineering_execution_plan_exists() -> None:
    assert (ROOT / "docs" / "engineering-execution-plan.md").exists()


def test_engineering_execution_plan_mentions_critical_path() -> None:
    content = (ROOT / "docs" / "engineering-execution-plan.md").read_text(encoding="utf-8")
    assert "MVP Critical Path" in content
    assert "Sprint 1" in content
    assert "Acceptance criteria" in content
