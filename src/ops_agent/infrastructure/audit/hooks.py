from __future__ import annotations

from ops_agent.audit_logging import StructuredLogEvent, build_log_event


def case_event_log(*, trace_id: str, case_id: str, event_name: str, **details: object) -> StructuredLogEvent:
    return build_log_event(event_name=event_name, trace_id=trace_id, case_id=case_id, **details)
