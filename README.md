# TaxOS

A simple receipt-tracking tool.

The goal is to simplify tax returns by tracking receipts across user-defined buckets.

The backend will by python/grpc but we will implement that later -- lets just keep it in mind, if at affects the design/schema.

We'd like to use modern web technologies, e.g Vite. 

## Landing page

Upon logging in (auth will be handled later, lets just stub it for now), the user will get to their dashboard.

The dashboard will show a list of all buckets and the total amount allocated to each.

Date filters can be applied to the dashboard to show totals for a given time period. Default is current year.

Clicking on a bucket will take the user to a page showing all receipts in that bucket for the selected time period (carry the filter over).

User can show/hide buckets that have no receipts in them for the selected time period.

The date filter is applied to the receipts shown in the bucket list.

## Buckets

A bucket represents an allocation of funds spent on a particular concept, e.g. shipping or materials.

A bucket has a name (set by the user) and a system-generated guid (we'll use UUIDs, can generate in the frontend for now).

A bucket contains many receipts.

## Receipt

A receipt...

- represents a transaction with a vendor
- has a guid (system-generated)
- has a datetime (user-provided, timezone-aware)
- has a total (user-provided)
- has a list of buckets with amounts allocated to each (buckets are referenced by guid)
- has an optional ref (user-provided)
- has optional notes (user-provided)
- has a file (user-provided, optional)

### Allocations

A receipt's allocations can be edited at any time.

The sum of all allocations must equal the receipt total.

A hidden "unallocated" bucket is maintained. If the user doesn't allocate the full amount, the remainder is added to the unallocated bucket.

When adding a new receipt, the unallocated bucket is not shown. The user can choose to allocate the full amount to one bucket, or split it between multiple buckets.

When selecting allcoations in the UI, the user can click on an icon for the bucket on the left to toggle it off (set back to 0). Clicking another bucket will perform an even split (50/50); clicking a third will do a 3-way split, etc.

The user can click on a $ to manually edit (e.g. they know one bucket should have $20 so they enter it directly instead of using the % slider).

We do not persist any % values, only the dollar amounts; % is simply a visual aid for the user.

## Receipt-in-hand flow

The user has a receipt from a transaction with a vendor (e.g. purchased inventory, materials or shipping label).

User drags receipt file on an "Upload Receipt" zone in the UI.

<!-- TODO later: Receipt pdf is uploaded to the backend -->

Modal opens, allowing user to add info about the transaction.

In the modal are listed all of the user's configured buckets.

User can input the total receipt amount and then click on sliders for each of the buckets to set the percent contribution to that bucket from the total.

e.g.

```yaml
receipt:
  vendor: dutch country market
  date: 2026-01-31
  total: 135.78
  buckets:
    ebay-inventory: .25
    groceries: .75
```

All buckets start out at 0%.

When the user clicks the slider, they see the $ share of the total based on the selected %.

They can click on an icon for the bucket on the left to toggle it off (set back to 0).

While no bucket is selected, clicking the left icon for one will assign 100% to it. Clicking another bucket will perform an even split (50/50); clicking a third will do a 3-way split, etc.

The user can click on a $ to manually edit (e.g. they know one bucket should have $20 so they enter it directly instead of using the % slider).

The receipt date in the model is prefilled with the current date+time and can be changed with a calendar picker. It is stored as an iso8601 timestamp with offset. The user's current timezone is also stored (e.g. America/New_York).

There is an optional field for a receipt ref (e.g. transaction number from the vendor).

There is an optional notes field.

The user can click save as soon at any time to submit the form.
