from uuid import UUID

from uuid_extensions import uuid7str


def uuid7() -> UUID:
  return UUID(uuid7str())
