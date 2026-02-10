# To Do: Taxos Development

## Summary

Currently, data for added receipts is primarily stored in localstorage on the frontend. We send it to the backend, but we don't load receipts from the backend. so if i clear out my localtorage, all my receipts are gone.

Also, I notice that we are not actually sending the bucket totals and receipt counts in the listbuckets response.

To keep in sync, lets do this:

- when the page loads, load buckets **once** (this is the auth check; if the token is good, we get buckets and we store them in localstorage)
  - this does not return the actual receipts in the buckets
- when date filters change, reload buckets (to refresh totals and counts in the bucket summary)
- when user opens a bucket, load receipts **for that bucket only** (or the unallocated bucket, if that was opened, but leaving out the bucket id from the request)
  - this will include the current date filter
- if user saves changes to a receipt (or creates one), the localstorage representation should be updated to the response form the backend
  - this gets the receipt details for that bucket (everything allocated to it). At that point, we could store them in localstorage. I think it probably makes sense to keep a guid-indexed dict of receipts in localstorage, so we can quickly add/update/remove them based on api calls.

## Progress

### Receipt & Bucket Data Management
- ✅ Added `ListReceipts` RPC to proto with optional `bucket_guid` parameter for bucket-filtered receipt loading
- ✅ Updated `ListBuckets` to calculate and return `total_amount` and `receipt_count` summaries
- ✅ Changed frontend receipt storage to guid-indexed dict (`Record<string, Receipt>`) for efficient updates
- ✅ Dashboard now uses API-provided bucket summaries instead of client-side calculation
- ✅ BucketDetail loads receipts via `ListReceipts` API when bucket is selected
- ✅ Fixed infinite render loop by wrapping context functions in `useCallback`

### Backend Refactoring
- ✅ Replaced `UnallocatedReceiptRepo` with unified `ReceiptRepo`
- ✅ Updated `LoadReceiptRepo` to support optional bucket filtering with `bucket` parameter
- ✅ Changed allocation data structure from tuples `[(bucket_guid, amount)]` to `Allocation` objects with `{bucket: BucketRef, amount: float}`
- ✅ Updated all API handlers (`create_receipt`, `update_receipt`, `list_receipts`, `list_buckets`, `list_unallocated_receipts`) to use new `ReceiptRepo` and `Allocation` structure

## Remaining Tasks

### Testing & Validation
- [ ] End-to-end testing of receipt creation with allocations
- [ ] Verify bucket summary calculations are correct
- [ ] Test date filtering on ListBuckets and ListReceipts
- [ ] Confirm localStorage stays in sync when receipts are created/updated/deleted

## Known issues

the frontend currently just spams listbuckets continuously very fast as soon as the page loads
