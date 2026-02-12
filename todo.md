# To Do: Taxos Development

## Today's Task

The flow of data we have now is inconsistent.

We need to convert the current ListBucketsRequest into GetDashboardRequest, and add a domain action for it at taxos/tenant/dashboard/get. We can define the shape in taxos/tenant/dashboard/entity.py (it is a capable entity.)

We'll return a list of bucket summaries (allocation total $ + count), along with all unallocated receipts (full details; frontend can then render the special unallocated bucket).

We can then make the ListReceiptsRequest require a bucket (as unallocated will be handled explicitly by the dashboard). This will make our domain clearer.

