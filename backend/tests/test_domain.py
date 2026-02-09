from datetime import datetime

import pytest
from google.protobuf.timestamp_pb2 import Timestamp
from scaf.cli import call
from taxos.access.token.generate.command import GenerateAccessToken
from taxos.access.token.revoke.command import RevokeToken
from taxos.bucket.entity import Bucket
from taxos.bucket.repo.entity import BucketRepo
from taxos.context.entity import Context
from taxos.context.tools import set_context
from taxos.receipt.entity import Receipt
from taxos.tenant.create.command import CreateTenant
from taxos.tenant.delete.command import DeleteTenant
from taxos.tenant.entity import TenantRef
from taxos.tenant.unallocated_receipt.repo.entity import UnallocatedReceiptRepo

from dev import BACKEND_ROOT


@pytest.fixture
def test_context():
  """Create a test tenant and generate access token, cleanup after test"""
  tenant = CreateTenant(name="Test Tenant").execute()
  access_token = GenerateAccessToken(tenant).execute()
  context = Context(tenant, access_token)
  set_context(context)

  yield context

  # Cleanup
  try:
    RevokeToken(hash=access_token.key).execute()
    DeleteTenant(TenantRef(tenant.guid.hex)).execute()
  except Exception as e:
    print(f"Cleanup warning: {e}")


def scaf(action: str, *args):
  return call(BACKEND_ROOT, action, *args)


def ensure_bucket_created(name: str) -> Bucket:
  result: Bucket | None = scaf(
    "taxos/bucket/create",
    f"{name} {datetime.now().isoformat()}",
  )
  assert isinstance(result, Bucket), f"Expected Bucket instance, got {type(result)}"
  bucket: Bucket = result
  assert bucket.name.startswith(name)
  return bucket


def ensure_bucket_updated(original_bucket: Bucket) -> Bucket:
  result = scaf(
    "taxos/bucket/update",
    original_bucket.guid.hex,
    f"Updated Test Bucket {datetime.now().isoformat()}",
  )
  assert isinstance(result, Bucket), f"Expected Bucket instance, got {type(result)}"
  bucket: Bucket = result
  assert bucket.guid == original_bucket.guid
  assert bucket.name.startswith("Updated Test Bucket")
  return bucket


def ensure_bucket_exists(bucket: Bucket):
  result = scaf("taxos/bucket/repo/load")
  assert isinstance(result, BucketRepo), f"Expected BucketRepo, got {type(result)}"
  bucket_list: list[Bucket] = list(result.index.values())
  assert any(b.guid == bucket.guid for b in bucket_list), "Created bucket not found in list"


def ensure_unallocated_receipt_repo() -> UnallocatedReceiptRepo:
  result = scaf("taxos/tenant/unallocated_receipt/repo/load")
  assert isinstance(result, UnallocatedReceiptRepo), f"Expected UnallocatedReceiptRepo, got {type(result)}"
  return result


def ensure_no_unallocated_receipts():
  repo = ensure_unallocated_receipt_repo()
  assert not repo.unallocated_receipts, "Unallocated receipts should be empty"


def ensure_unallocated_receipt(receipt: Receipt, unallocated_amount: float = 0):
  repo = ensure_unallocated_receipt_repo()
  unallocated_receipt = repo.index_by_guid.get(receipt.guid)
  assert unallocated_receipt is not None, "Receipt should be unallocated"
  assert unallocated_receipt.unallocated_amount == unallocated_amount, "Unallocated amount should equal receipt total"


def ensure_receipt_created(vendor: str, total: float, vendor_ref: str = "TEST-REF") -> Receipt:
  now = Timestamp()
  now.GetCurrentTime()
  result = scaf(
    "taxos/receipt/create",
    vendor,
    str(total),
    now.ToJsonString(),
    "America/New_York",
    f"--vendor-ref={vendor_ref}",
    "--notes=Test receipt",
    "--hash=test-hash",
  )
  assert isinstance(result, Receipt), f"Expected Receipt instance, got {type(result)}"
  receipt: Receipt = result
  assert receipt.vendor == vendor
  assert receipt.total == total
  assert receipt.vendor_ref == vendor_ref
  return receipt


def ensure_receipt_deleted(receipt: Receipt):
  result = scaf("taxos/receipt/delete", receipt.guid.hex)
  assert result is True, f"Expected True from receipt delete, got {result}"
  repo = ensure_unallocated_receipt_repo()
  assert receipt.guid not in repo.index_by_guid, "Deleted receipt should not be in unallocated repo"


def ensure_bucket_deleted(bucket: Bucket):
  result = scaf("taxos/bucket/delete", bucket.guid.hex)
  assert result is True, f"Expected True from bucket delete, got {result}"
  try:
    ensure_bucket_exists(bucket)
  except AssertionError as e:
    assert "not found" in str(e), "Expected bucket to be deleted, but it still exists"


@pytest.mark.integration
def test_happy_path(test_context):
  """Full API integration test including tenant authentication"""
  tenant = test_context.tenant
  assert tenant is not None, "Tenant should be set in context"
  assert tenant.name == "Test Tenant", f"Expected tenant name 'Test Tenant', got '{tenant.name}'"
  token = test_context.access_token
  assert token is not None, "Access token should be set in context"

  created_bucket = ensure_bucket_created("Test Bucket")
  updated_bucket = ensure_bucket_updated(created_bucket)
  assert updated_bucket.guid == created_bucket.guid, "Bucket GUID should not change on update"

  ensure_bucket_exists(updated_bucket)
  ensure_no_unallocated_receipts()

  receipt = ensure_receipt_created("THE AWESOME STORE!", 12.34)
  ensure_unallocated_receipt(receipt, 12.34)

  ensure_receipt_deleted(receipt)

  ensure_bucket_deleted(created_bucket)
