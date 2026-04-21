from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypedDict

from pydantic import ValidationError

from app.schemas.processing import IdentityDocumentExtraction


class ExtractionState(TypedDict, total=False):
    image_data_url: str
    attempt_count: int
    retry_prompt: bool
    raw_output: dict[str, Any]
    validated_output: dict[str, Any]
    normalized_output: dict[str, Any]
    validation_error: str | None


LLMExtractionCall = Callable[[str, bool, dict[str, Any]], dict[str, Any]]


def preprocess_node(state: ExtractionState) -> ExtractionState:
    if not state.get("image_data_url"):
        return {**state, "validation_error": "image_data_url is required."}
    return {**state, "validation_error": None}


def extraction_node(state: ExtractionState, llm_call: LLMExtractionCall) -> ExtractionState:
    attempt_count = state.get("attempt_count", 0) + 1
    raw_output = llm_call(
        state["image_data_url"],
        bool(state.get("retry_prompt")),
        IdentityDocumentExtraction.model_json_schema(),
    )
    return {**state, "attempt_count": attempt_count, "raw_output": raw_output}


def validation_node(state: ExtractionState) -> ExtractionState:
    try:
        validated = IdentityDocumentExtraction.model_validate(state.get("raw_output", {}))
    except ValidationError as exc:
        return {**state, "validation_error": exc.json(), "validated_output": {}}
    return {
        **state,
        "validation_error": None,
        "validated_output": validated.model_dump(mode="json"),
    }


def retry_node(state: ExtractionState) -> ExtractionState:
    return {**state, "retry_prompt": True}


def normalization_node(state: ExtractionState) -> ExtractionState:
    normalized = IdentityDocumentExtraction.model_validate(state["validated_output"])
    return {**state, "normalized_output": normalized.model_dump(mode="json")}


def output_node(state: ExtractionState) -> ExtractionState:
    return state


def validation_route(state: ExtractionState) -> str:
    if state.get("validation_error") and state.get("attempt_count", 0) < 2:
        return "retry_node"
    if state.get("validation_error"):
        return "output_node"
    return "normalization_node"


def build_identity_extraction_graph(llm_call: LLMExtractionCall):
    from langgraph.graph import END, StateGraph

    graph = StateGraph(ExtractionState)
    graph.add_node("preprocess_node", preprocess_node)
    graph.add_node("extraction_node", lambda state: extraction_node(state, llm_call))
    graph.add_node("validation_node", validation_node)
    graph.add_node("retry_node", retry_node)
    graph.add_node("normalization_node", normalization_node)
    graph.add_node("output_node", output_node)

    graph.set_entry_point("preprocess_node")
    graph.add_edge("preprocess_node", "extraction_node")
    graph.add_edge("extraction_node", "validation_node")
    graph.add_conditional_edges(
        "validation_node",
        validation_route,
        {
            "retry_node": "retry_node",
            "normalization_node": "normalization_node",
            "output_node": "output_node",
        },
    )
    graph.add_edge("retry_node", "extraction_node")
    graph.add_edge("normalization_node", "output_node")
    graph.add_edge("output_node", END)
    return graph.compile()
