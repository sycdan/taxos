from datetime import datetime

import pytest
from google.protobuf.timestamp_pb2 import Timestamp
from taxos.access.token.generate.command import GenerateAccessToken
from taxos.access.token.revoke.command import RevokeToken
from taxos.bucket.create.command import CreateBucket
from taxos.bucket.delete.command import DeleteBucket
from taxos.bucket.entity import Bucket
from taxos.bucket.repo.entity import BucketRepo
from taxos.bucket.repo.load.query import LoadBucketRepo
from taxos.bucket.update.command import UpdateBucket
from taxos.context.entity import Context
from taxos.context.tools import set_context
from taxos.receipt.create.command import CreateReceipt
from taxos.receipt.delete.command import DeleteReceipt
from taxos.receipt.entity import Receipt
from taxos.receipt.repo.load.command import LoadReceiptRepo
from taxos.tenant.create.command import CreateTenant
from taxos.tenant.dashboard.get.query import GetDashboard
from taxos.tenant.delete.command import DeleteTenant
from taxos.tenant.entity import TenantRef
from taxos.tenant.list_receipts.query import ListReceipts
from taxos.tenant.unallocated_receipt.check.command import CheckUnallocatedReceipt

MONTH_KEY = datetime.now().strftime("%Y-%m")


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


def ensure_bucket_created(name: str) -> Bucket:
  result: Bucket | None = CreateBucket(
    name=f"{name} {datetime.now().isoformat()}",
  ).execute()
  assert isinstance(result, Bucket), f"Expected Bucket instance, got {type(result)}"
  bucket: Bucket = result
  assert bucket.name.startswith(name)
  return bucket


def ensure_bucket_updated(original_bucket: Bucket) -> Bucket:
  result = UpdateBucket(
    original_bucket.guid.hex,
    f"Updated Test Bucket {datetime.now().isoformat()}",
  ).execute()
  assert isinstance(result, Bucket), f"Expected Bucket instance, got {type(result)}"
  bucket: Bucket = result
  assert bucket.guid == original_bucket.guid
  assert bucket.name.startswith("Updated Test Bucket")
  return bucket


def ensure_bucket_exists(bucket: Bucket):
  result = LoadBucketRepo().execute()
  assert isinstance(result, BucketRepo), f"Expected BucketRepo, got {type(result)}"
  bucket_list: list[Bucket] = list(result.index.values())
  assert any(b.guid == bucket.guid for b in bucket_list), "Created bucket not found in list"


def get_receipt_list(month_key: str = MONTH_KEY, bucket="") -> list[Receipt]:
  result = ListReceipts(months=[month_key], bucket=bucket).execute()
  assert isinstance(result, list), f"Expected Receipt list, got {type(result)}"
  return result


def ensure_unallocated_receipt(receipt: Receipt, unallocated_amount: float = 0):
  dashboard = GetDashboard(months=[MONTH_KEY]).execute()
  assert receipt in dashboard.unallocated, "Receipt should be in unallocated list"
  unallocated_receipt = CheckUnallocatedReceipt(receipt).execute()
  assert unallocated_receipt is not None, "Receipt should be unallocated"
  assert unallocated_receipt.unallocated_amount == unallocated_amount, "Unallocated amount should equal receipt total"


def ensure_receipt_created(vendor: str, total: float, vendor_ref: str = "TEST-REF") -> Receipt:
  now = Timestamp()
  now.GetCurrentTime()
  result = CreateReceipt(
    vendor,
    total,
    now.ToJsonString(),
    "America/New_York",
    vendor_ref=vendor_ref,
    notes="Test receipt",
  ).execute()
  assert isinstance(result, Receipt), f"Expected Receipt instance, got {type(result)}"
  receipt: Receipt = result
  assert receipt.vendor == vendor
  assert receipt.total == total
  assert receipt.vendor_ref == vendor_ref
  return receipt


def ensure_receipt_deleted(receipt: Receipt):
  result = DeleteReceipt(receipt).execute()
  assert result is True, f"Expected True from receipt delete, got {result}"
  repo = LoadReceiptRepo().execute()
  assert repo.get_by_ref(receipt.guid) is None, "Receipt should be deleted from repo"


def ensure_bucket_deleted(bucket: Bucket):
  result = DeleteBucket(bucket.guid.hex).execute()
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

  receipt = ensure_receipt_created("THE AWESOME STORE!", 12.34)
  ensure_unallocated_receipt(receipt, 12.34)

  ensure_receipt_deleted(receipt)

  ensure_bucket_deleted(created_bucket)
