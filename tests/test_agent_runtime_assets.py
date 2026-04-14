from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ops_agent.agents.runtime import AgentRuntimeService
from ops_agent.prompt_registry import PROMPT_REGISTRY


ROOT = Path(__file__).resolve().parents[1]


def test_prompt_registry_schema_files_exist() -> None:
    schema_dir = ROOT / "contracts" / "jsonschema"

    for prompt_definition in PROMPT_REGISTRY.values():
        assert (schema_dir / prompt_definition.schema_file).exists()


def test_safe_reasoning_summary_is_bounded() -> None:
    summary = AgentRuntimeService._safe_reasoning_summary(
        raw_summary="word " * 300,
        max_chars=120,
    )
    assert summary is not None
    assert len(summary) == 120
    assert summary.endswith("...")
