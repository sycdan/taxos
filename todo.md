# To Do: Taxos Development

## Today's Task

we need to add a test to the vendor flow spec
we should create a receipt, then switch to a different year (with no receipts) and make sure that the vendor card does not show up, then click show empty and enture it shows up with no receipts

we need to start using vendorGuid for queries instead of name

we need to add helpers in the flow tests for thigns like adding receipts, to reduce code duplication. the helpers should also perform test asserts so we know if that part of the flow breaks.

do we still need the getDashbaord concept? that was added when we were using protobuf & connectrpc, and needed to optimize query shapes