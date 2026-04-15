# Worker

Background processing runtime for asynchronous document workflows.

Use this app for:

- OCR job execution
- document parsing and classification tasks
- extraction and validation task orchestration
- retry-safe workflow transitions
- provider adapter execution with auditable job status changes

The worker should never make silent business decisions. It produces explicit task results and audit events for the backend to persist and expose.
