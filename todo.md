# To Do: Taxos Development

## Today's Task

can we revisit the unallocated bucket concept?

if we are not retrieving receipts by bucket, I don't think we need a constant ID for the "unallocated" bucket -- the FE would just look at each receipt and determing if it's fully allocated, and if not then render it in the unallocated section
