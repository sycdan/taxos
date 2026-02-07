# Today's Task

We need the grpc server to return all unallocated receipts for the tenant when the user clicks on the unallocated bucket on the frontend.

## Implementation Plan

### Protocol Buffers

#### 1. Update proto definitions
- [x] Add service method to TaxosApi service
- [x] Add request message with optional date filtering
- [x] Add response message returning list of receipts
- [x] Regenerate Python gRPC stubs (dev.gen-proto)

### Backend Changes

#### 2. Add new gRPC service method
- [x] Add `ListUnallocatedReceipts` method to `taxos_service.proto`
- [x] Define `ListUnallocatedReceiptsRequest` and `ListUnallocatedReceiptsResponse` messages
- [x] Include date filtering (start_date, end_date) like other list operations

#### 3. Implement backend handler
- [x] Create `list_unallocated_receipts/` module in `backend/taxos/`
- [x] Create `query.py` with `ListUnallocatedReceipts` dataclass
- [x] Logic: Load all receipts from tenant's receipts dir; filter for unallocated receipts (no allocations or sum of allocations < total)
- [x] Return receipts sorted by date (newest first)

#### 4. Add gRPC endpoint
- [x] Add handler method in `connect_http_server.py`
- [x] Route: `POST /taxos.v1.TaxosApi/ListUnallocatedReceipts`
- [x] Include authentication via `@require_auth` decorator
- [x] Handle date filtering

### Frontend Changes

#### 5. Add API client method
- [ ] Add `listUnallocatedReceipts` method to `frontend/src/api/client.ts`
- [ ] Include date range parameters matching other list methods

#### 6. Update context logic
- [ ] Modify `TaxosContext.tsx` to call backend for unallocated receipts
- [ ] Replace current client-side filtering logic
- [ ] Ensure proper error handling and loading states

### Testing

#### 7. Add tests
- [ ] Unit tests for `ListUnallocatedReceipts` query class
- [ ] Integration tests in `test_api.py`
- [ ] Test edge cases (all allocated, partial allocations, zero-amount receipts)

### Technical Details

**Unallocated Receipt Definition:**
A receipt is considered unallocated if:
- `len(allocations) == 0` (new empty receipts), OR
- `sum(allocation.amount for allocation in allocations) < total`

**Date Filtering:**
- Use same date filtering logic as `ListBuckets`
- Filter by receipt.date within start_date and end_date range
