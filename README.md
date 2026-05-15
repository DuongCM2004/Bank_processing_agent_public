# Banking Document Processing Agent

This repository contains the first implementation slice for the Ops Agent plan:

- FastAPI backend skeleton
- explicit banking case/document/review schemas
- workflow-safe state transitions
- append-only audit events
- reviewer task handling
- production specification for LLM-based document information extraction

## Current scope

This is not the full platform. The current implementation provides the MVP backend foundation needed to start parallel work across backend, frontend, AI, QA, and security.

The current Documents module target is an inference-only LLM extraction workflow: upload document, store raw file, queue extraction, preprocess with Python/Pillow, call OpenAI GPT-4o or GPT-4o-mini Vision through LangGraph, enforce strict JSON schema, retry once on validation failure, normalize into an editable review table, persist only approved reviewed data, and maintain audit/UUID traceability.

Canonical spec: [docs/production-llm-document-extraction-backend-spec.md](docs/production-llm-document-extraction-backend-spec.md)

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

- GPT-4o Vision extraction adapter
- LangGraph extraction orchestration
- persistent relational database
- object storage
- authentication middleware
- reviewer UI

## Run locally

```powershell
py -m pip install -e .[dev]
py -m uvicorn ops_agent.main:app --reload --app-dir src
```

## Run Local Docker Stack

```powershell
docker compose up --build
```

See [infra/docker/README.md](infra/docker/README.md) for ports, volumes, local networking, and reset commands.

## Test

```powershell
py -m pytest
```

## Target Monorepo Structure

The repo now includes a target MVP-first monorepo scaffold under `apps/`, `packages/`, `infra/`, and `tooling/`.
Use [docs/repository-structure.md](docs/repository-structure.md) as the source of truth for folder ownership, naming conventions, and migration targets.

## Demo

Watch demo here: [Project Demo](https://youtu.be/Wz2VC6cVUlc)
