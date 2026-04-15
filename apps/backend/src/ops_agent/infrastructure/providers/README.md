## Provider Notes

These interfaces are intentionally small and synchronous for the MVP.

- Keep adapters thin: translate between external provider payloads and the DTOs in `interfaces.py`.
- Preserve confidence and evidence references whenever the upstream provider exposes them.
- Do not leak vendor-specific response shapes outside the adapter layer.
- When a real provider is asynchronous, keep the public interface stable and let the adapter handle polling or job reconciliation internally, or introduce an async task wrapper at the orchestration boundary rather than pushing vendor semantics into services.
- Classification should remain advisory unless the platform has a dedicated classification result entity and review controls for overwriting document types.
- Validation engines should emit structured findings, not persistence models, so policy logic stays swappable across deterministic rules, external policy services, or hybrid engines.
