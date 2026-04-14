# Banking Document Processing Agent

This repository contains the first implementation slice for the Ops Agent plan:

- FastAPI backend skeleton
- explicit banking case/document/review schemas
- workflow-safe state transitions
- append-only audit events
- reviewer task handling

## Current scope

This is not the full platform. The current implementation provides the MVP backend foundation needed to start parallel work across backend, frontend, AI, QA, and security.

### Included

- case creation
- document attachment metadata
- case status tracking
- review task queue
- field correction actions
- escalation actions
- revalidation trigger
- audit event retrieval

### Not yet included

- OCR integration
- extraction/classification model adapters
- persistent relational database
- object storage
- authentication middleware
- reviewer UI

## Run locally

```powershell
py -m pip install -e .[dev]
py -m uvicorn ops_agent.main:app --reload --app-dir src
```

## Test

```powershell
py -m pytest
```
