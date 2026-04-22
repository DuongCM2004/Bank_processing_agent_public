# Frontend Test Scaffold

Frontend tests for the Ops Agent live under `apps/frontend/tests` and use React Testing Library with Vitest.

## Conventions

- `tests/*.test.tsx`: current MVP component and page behavior specs.
- `tests/unit/`: reserved for pure presentational/component tests as the suite expands.
- `tests/integration/`: reserved for page-level and multi-component workflow tests.
- `tests/render.tsx`: shared render helper with router and React Query providers.
- `tests/mock-api.ts`: reusable mock query states and typed API data builders.

## What to test first

- UX-critical reviewer paths: case queue, case workspace, extraction review, findings review.
- Async states: loading, error, retry, and empty results.
- Reviewer-visible clarity: blocking findings, uncertain extraction values, manual review cues, and navigation affordances.

## Mocking approach

- Prefer mocking feature hooks over mocking `fetch` directly for component and page tests.
- Use typed builders from `tests/mock-api.ts` so contract changes fail in one place.
- Keep tests focused on user-visible behavior instead of implementation details.
