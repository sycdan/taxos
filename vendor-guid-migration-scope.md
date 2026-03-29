# Vendor GUID Migration Scope

## Goal

Move vendor selection, filtering, and detail views onto vendor GUIDs end to end, instead of relying on vendor name strings as the primary identity.

## Why This Is Separate Work

The current app is mixed-mode:

- Vendor management already updates vendors by GUID.
- Vendor dashboard summaries are rebuilt from `receipt.vendor` name strings.
- Vendor detail navigation still selects a vendor by name.
- The backend `receipts(vendor:)` resolver still accepts either GUID or name for compatibility.

That means the remaining work is a data-flow migration, not a single query swap.

## Current Gaps

### Frontend

- [frontend/src/contexts/TaxosContext.tsx](frontend/src/contexts/TaxosContext.tsx) derives `vendorSummaries` from receipt vendor names instead of a vendor identity map.
- [frontend/src/components/Dashboard.tsx](frontend/src/components/Dashboard.tsx) calls `onSelectVendor(vendor.name)` even though the card model already carries `vendor.id`.
- [frontend/src/components/VendorDetail.tsx](frontend/src/components/VendorDetail.tsx) accepts a vendor name string and loads receipts with that value.
- [frontend/src/App.tsx](frontend/src/App.tsx) stores `selectedVendor` as a string that currently represents the vendor name, not a GUID.
- [frontend/src/types.ts](frontend/src/types.ts) has no vendor reference on receipts, only the display name.

### Backend

- [backend/api/graphql_server.py](backend/api/graphql_server.py) has a compatibility branch in `receipts(vendor:)` that accepts both GUID and vendor name.
- Receipt payloads currently expose vendor display name, but not a stable vendor reference the frontend can use for summary joins.

### E2E Coverage

- Vendor rename is not currently exercisable through the main app flow because [frontend/src/components/VendorManager.tsx](frontend/src/components/VendorManager.tsx) exists but is not rendered from [frontend/src/App.tsx](frontend/src/App.tsx).

## Proposed Workstreams

1. Add stable vendor references to receipt-shaped frontend data.
   - Expose vendor GUID on receipt responses.
   - Thread that through [frontend/src/api/client.ts](frontend/src/api/client.ts), [frontend/src/types.ts](frontend/src/types.ts), and [frontend/src/contexts/TaxosContext.tsx](frontend/src/contexts/TaxosContext.tsx).

2. Switch vendor summaries and selection to GUIDs.
   - Build vendor summaries from the vendor list keyed by GUID.
   - Use vendor GUID for dashboard selection.
   - Store `selectedVendor` as vendor GUID in [frontend/src/App.tsx](frontend/src/App.tsx).

3. Switch vendor detail loading to GUIDs.
   - Update [frontend/src/components/VendorDetail.tsx](frontend/src/components/VendorDetail.tsx) and context methods to request receipts by GUID.
   - Preserve display name separately from identity.

4. Remove compatibility query paths.
   - Once the frontend exclusively passes GUIDs, remove name-based vendor filtering from [backend/api/graphql_server.py](backend/api/graphql_server.py).

5. Expose or intentionally remove vendor rename UI.
   - Either render [frontend/src/components/VendorManager.tsx](frontend/src/components/VendorManager.tsx) in the app and add E2E coverage, or delete the dead component and implement rename somewhere else.

## Non-Goals

- Reworking receipt creation UX.
- Changing vendor naming rules or deduplication behavior.
- General cleanup unrelated to vendor identity.

## Risks

- Any place that still assumes `receipt.vendor` is the identity key will quietly regress rename behavior.
- Mixed data during migration can create mismatches between summary cards and vendor detail results.
- The rename-flow test should not be added until there is a user-reachable rename surface.

## Acceptance Criteria

- Vendor dashboard cards and vendor detail routes use vendor GUIDs as identity.
- Receipt filtering by vendor uses GUID only.
- The backend no longer needs name-based vendor filtering compatibility.
- A user-reachable vendor rename flow exists and has E2E coverage.