"""Special GUIDs representing domain concepts, not instances (never persisted).

These should be updated when our domain implementation for these concepts changes.

The format is:
-  8 hex digits for the concept identifier (e.g. 0410c8ed for the unallocated bucket)
-  4 hex digits for the year the concept was added/changed (aka major version)
-  4 hex digits for the mmdd (aka minor version)
-  4 hex digits for the time (aka patch version)
- 12 hex digits for the type (e.g. 000000000001 for singleton entities)

If a concept changes:
- copy the last version of the constant to the line below
- update the constant's value with the current date and time

If a contract is broken (e.g. field removed, field type changed, other breaking change):
- increment the version on the new row (e.g. V1 above V2)
"""

from uuid import UUID


UNSPECIFIED = UUID("00000000-0000-0000-0000-000000000000")

UNALLOCATED_BUCKET_V1_SINGLETON = UUID("0410c8ed-2026-0328-1251-000000000001")

LIST_RECEIPTS_QUERY = UUID("11572ec8-2024-0601-0000-000000000000")
LIST_RECEIPTS_HANDLER = UUID("11572ec8-2024-0601-0000-000000000001")
LIST_RECEIPTS_RESULT = UUID("11572ec8-2024-0601-0000-000000000002")
