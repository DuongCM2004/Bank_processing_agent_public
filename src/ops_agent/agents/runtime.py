from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from ops_agent.agents.runtime_models import (
    AgentFailure,
    AgentInvocationRequest,
    AgentValidatedResult,
)
from ops_agent.audit_logging import build_agent_audit_details
from ops_agent.prompt_registry import get_prompt_definition


class StructuredAgentAdapter(Protocol):
    def generate_structured(self, request: AgentInvocationRequest) -> dict[str, Any]: ...


class OutputSchemaValidator(Protocol):
    def validate(self, *, schema_path: Path, payload: dict[str, Any]) -> None: ...


class AgentRuntimeError(RuntimeError):
    def __init__(self, failure: AgentFailure) -> None:
        super().__init__(failure.safe_message)
        self.failure = failure


class AgentRuntimeService:
    def __init__(self, *, schema_root: Path, validator: OutputSchemaValidator) -> None:
        self._schema_root = schema_root
        self._validator = validator

    def invoke(
        self,
        *,
        request: AgentInvocationRequest,
        adapter: StructuredAgentAdapter,
    ) -> AgentValidatedResult:
        prompt_definition = get_prompt_definition(request.capability)
        self._assert_request_matches_registry(request=request, prompt_definition=prompt_definition)

        try:
            output_payload = adapter.generate_structured(request)
            self._validator.validate(
                schema_path=self._schema_root / request.schema_file,
                payload=output_payload,
            )
        except Exception as exc:
            raise AgentRuntimeError(
                AgentFailure(
                    capability=request.capability,
                    prompt_id=request.prompt_id,
                    prompt_version=request.prompt_version,
                    schema_file=request.schema_file,
                    error_code="agent_output_validation_failed",
                    retryable=False,
                    safe_message="Agent output could not be validated against the declared schema.",
                    details={"exception_type": type(exc).__name__},
                )
            ) from exc

        result = AgentValidatedResult(
            capability=request.capability,
            prompt_id=request.prompt_id,
            prompt_version=request.prompt_version,
            schema_name=request.schema_name,
            schema_file=request.schema_file,
            model_name=request.model_name,
            model_version=output_payload.get("model_version"),
            status=output_payload["status"],
            escalation_target=output_payload.get("escalation_target", "none"),
            confidence_score=output_payload.get("confidence_score"),
            reason_codes=output_payload.get("reason_codes", []),
            evidence_refs=output_payload.get("evidence_refs", []),
            output_payload=output_payload,
            reasoning_summary=self._safe_reasoning_summary(
                raw_summary=output_payload.get("reasoning_summary"),
                max_chars=prompt_definition.reasoning_summary_max_chars,
            ),
            raw_output_artifact_id=output_payload.get("raw_output_artifact_id"),
        )
        self._assert_result_matches_policy(result=result, request=request)
        return result

    def build_audit_details(self, *, result: AgentValidatedResult) -> dict[str, Any]:
        return build_agent_audit_details(
            capability=result.capability,
            prompt_id=result.prompt_id,
            prompt_version=result.prompt_version,
            schema_name=result.schema_name,
            schema_file=result.schema_file,
            model_name=result.model_name,
            model_version=result.model_version,
            status=result.status,
            escalation_target=result.escalation_target,
            confidence_score=result.confidence_score,
            reason_codes=result.reason_codes,
            evidence_refs=result.evidence_refs,
            reasoning_summary=result.reasoning_summary,
            raw_output_artifact_id=result.raw_output_artifact_id,
        )

    def _assert_request_matches_registry(self, *, request: AgentInvocationRequest, prompt_definition: Any) -> None:
        if request.prompt_id != prompt_definition.prompt_id:
            raise ValueError("Prompt id does not match the registered capability.")
        if request.prompt_version != prompt_definition.prompt_version:
            raise ValueError("Prompt version does not match the registered capability.")
        if request.schema_file != prompt_definition.schema_file:
            raise ValueError("Schema file does not match the registered capability.")
        if request.schema_name != prompt_definition.schema_name:
            raise ValueError("Schema name does not match the registered capability.")

    def _assert_result_matches_policy(
        self,
        *,
        result: AgentValidatedResult,
        request: AgentInvocationRequest,
    ) -> None:
        if result.status not in request.allowed_statuses:
            raise AgentRuntimeError(
                AgentFailure(
                    capability=request.capability,
                    prompt_id=request.prompt_id,
                    prompt_version=request.prompt_version,
                    schema_file=request.schema_file,
                    error_code="agent_status_out_of_policy",
                    retryable=False,
                    safe_message="Agent output status is outside the allowed policy for this capability.",
                    details={"status": result.status},
                )
            )
        if result.escalation_target not in request.allowed_escalation_targets:
            raise AgentRuntimeError(
                AgentFailure(
                    capability=request.capability,
                    prompt_id=request.prompt_id,
                    prompt_version=request.prompt_version,
                    schema_file=request.schema_file,
                    error_code="agent_escalation_target_out_of_policy",
                    retryable=False,
                    safe_message="Agent output escalation target is outside the allowed policy for this capability.",
                    details={"escalation_target": result.escalation_target},
                )
            )

    @staticmethod
    def _safe_reasoning_summary(*, raw_summary: str | None, max_chars: int) -> str | None:
        if not raw_summary:
            return None
        normalized = " ".join(raw_summary.split())
        if len(normalized) <= max_chars:
            return normalized
        return normalized[: max_chars - 3].rstrip() + "..."
