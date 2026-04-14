from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_testing_plan_and_helpers_exist() -> None:
    assert (ROOT / "docs" / "testing-scaffold-and-plan.md").exists()
    assert (ROOT / "tests" / "testkit.py").exists()
    assert (ROOT / "tests" / "stubs" / "providers.py").exists()


def test_core_case_fixtures_exist() -> None:
    fixture_dir = ROOT / "tests" / "fixtures" / "cases"
    assert (fixture_dir / "kyc_clean_case.json").exists()
    assert (fixture_dir / "ocr_low_confidence_case.json").exists()
    assert (fixture_dir / "workflow_retry_exhausted_case.json").exists()
