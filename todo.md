# To Do: Taxos Development

Currently, data for added receipts is primarily stored in localstore on the frontend. We send it to the backend, but we don't load receipts from the backend. so if i clear out my localtorage, all my receipts are gone.

Maybe we should not use localstorage for receipt data, unless we can keep it up to date with the backend somehow?

Similarly, if i save changes to a receipt (or create one), the localstorage representation should be updated to the response form the backend.

Also, I notice that we are not actually sending the bucket totals and receipt counts in the listbuckets response.

For good UX, I am thinking that when the page loads first time, or the user changes date filters, we should make a listbuckets call with the date filter, and use that to properly populate bucket summaries (without returning all receipt data).

Then, when they click on a bucket (or unallocated) we make another call to ListReceipts (again with the date filter) to get the receipt details for that bucket (everything allocated to it). At that point, we could store them in localstorage. I think it probably makes sense to keep a guid-indexed dict of receipts in localstorage, so we can quickly add/update/remove them based on api calls.

