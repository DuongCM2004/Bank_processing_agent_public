# Environment Layout

This directory documents the intended runtime environments for the Ops Agent.

## Local

- single-developer environment
- local Postgres, MinIO, Temporal, and Keycloak
- synthetic documents and stub providers only
- no production secrets

## Dev

- shared integration environment
- real auth, real persistence, stubbed or sandboxed OCR/AI providers
- used for feature branch validation and integration testing

## Staging

- production-like topology
- release candidate validation
- migration rehearsal
- controlled prompt/model release validation

## Production

- regulated banking operations environment
- controlled releases only
- strict audit, auth, and observability requirements
- prompt, rule, and model versions pinned separately from app image version
