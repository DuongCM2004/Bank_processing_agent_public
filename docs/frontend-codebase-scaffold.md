# Frontend Codebase Scaffold

## 1. Frontend project structure

```text
frontend/
  package.json
  tsconfig.json
  next-env.d.ts
  src/
    app/
      page.tsx
      login/page.tsx
      review-queue/page.tsx
      cases/
        page.tsx
        loading.tsx
        error.tsx
        [caseId]/
          layout.tsx
          page.tsx
          loading.tsx
          documents/page.tsx
          review/page.tsx
          audit/page.tsx
    components/
      app-shell.tsx
      access-entry-panel.tsx
      case-list-table.tsx
      case-header.tsx
      document-viewer-panel.tsx
      extraction-review-panel.tsx
      validation-issues-panel.tsx
      manual-correction-panel.tsx
      audit-history-panel.tsx
      review-task-table.tsx
      evidence-drawer.tsx
      loading-state.tsx
      error-state.tsx
      empty-state.tsx
      role-gate.tsx
    lib/
      types.ts
      mock-data.ts
      auth.ts
      navigation.ts
      state.ts
      api-client.ts
      api-cases.ts
      api-review.ts
      api-audit.ts
      api.ts
```

## 2. Routing structure

- `/`
  access entry
- `/login`
  auth handoff scaffold
- `/review-queue`
  reviewer work queue
- `/cases`
  case list
- `/cases/[caseId]`
  overview
- `/cases/[caseId]/documents`
  source document and evidence view
- `/cases/[caseId]/review`
  extraction, validation, and correction flow
- `/cases/[caseId]/audit`
  audit history

## 3. Page structure

- Access pages stay separate from review workspace routes.
- Case routes use nested layout so all case subpages share the same shell.
- Overview, documents, review, and audit are separate pages to keep large reviewer screens maintainable.

## 4. Shared component structure

- shell/navigation
- list/table views
- evidence/document panels
- extraction/validation panels
- correction flow
- audit timeline
- role gates
- loading/error/empty states

## 5. State management recommendation

- default: server components for route-level data
- local component state for correction drafts and viewer focus
- small auth/filter context only when needed
- add TanStack Query later when live polling and mutation invalidation become real

## 6. API integration layer structure

- `api-client.ts`
  low-level fetch
- `api-cases.ts`
  cases, results, documents
- `api-review.ts`
  review tasks and reviewer actions
- `api-audit.ts`
  audit retrieval
- `api.ts`
  compatibility re-export

## 7. Role-based view structure

- role helpers in `auth.ts`
- navigation shaping in `navigation.ts`
- render gating in `role-gate.tsx`
- roles assumed:
  `ops_reviewer`, `compliance_analyst`, `fraud_analyst`, `supervisor`, `platform_admin`

## 8. Key screens scaffold

- login/access entry: `app/page.tsx`, `app/login/page.tsx`
- case list: `app/cases/page.tsx`
- case details: `app/cases/[caseId]/page.tsx`
- document viewer: `components/document-viewer-panel.tsx`
- extraction review panel: `components/extraction-review-panel.tsx`
- validation/issues panel: `components/validation-issues-panel.tsx`
- manual correction flow: `components/manual-correction-panel.tsx`
- audit history view: `components/audit-history-panel.tsx`

## 9. UI state handling for loading/error/empty

- route loading: `app/cases/loading.tsx`, `app/cases/[caseId]/loading.tsx`
- route error: `app/cases/error.tsx`
- shared state components:
  `loading-state.tsx`, `error-state.tsx`, `empty-state.tsx`

## 10. Implementation stance

- optimize for source-vs-extracted comparison
- keep machine outputs visible during manual review
- preserve audit and evidence visibility in the primary reviewer flow
- use separate route pages instead of one massive case screen
