from datetime import datetime

import pytest
from google.protobuf.timestamp_pb2 import Timestamp
from scaf.cli import call
from taxos.access.token.generate.command import GenerateAccessToken
from taxos.access.token.revoke.command import RevokeToken
from taxos.bucket.entity import Bucket
from taxos.context.entity import Context
from taxos.context.tools import set_context
from taxos.tenant.create.command import CreateTenant
from taxos.tenant.delete.command import DeleteTenant
from taxos.tenant.entity import TenantRef

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


@pytest.mark.integration
def test_api_integration(test_context):
  """Full API integration test including tenant authentication"""
  tenant = test_context.tenant
  assert tenant is not None, "Tenant should be set in context"
  assert tenant.name == "Test Tenant", f"Expected tenant name 'Test Tenant', got '{tenant.name}'"
  token = test_context.access_token
  assert token is not None, "Access token should be set in context"

  # Create a bucket
  if result := scaf(
    "taxos/bucket/create",
    f"Test Bucket {datetime.now().isoformat()}",
  ):
    assert isinstance(result, Bucket), f"Expected Bucket instance, got {type(result)}"
    created_bucket: Bucket = result
    assert created_bucket.name.startswith("Test Bucket")

  # Update the bucket and make sure we get the updated name back, and the same guid
  if result := scaf(
    "taxos/bucket/update",
    created_bucket.guid.hex,
    f"Updated Test Bucket {datetime.now().isoformat()}",
  ):
    assert isinstance(result, Bucket), f"Expected Bucket instance, got {type(result)}"
    updated_bucket: Bucket = result
    assert updated_bucket.guid == created_bucket.guid
    assert updated_bucket.name.startswith("Updated Test Bucket")

  # The bucket should be listed in the tenant's buckets
  if result := scaf("taxos/tenant/list_buckets"):
    assert isinstance(result, list), f"Expected list of buckets, got {type(result)}"
    bucket_list: list[Bucket] = result
    assert any(b.guid == created_bucket.guid for b in bucket_list), "Created bucket not found in list"

  # Test: Create receipt
  now = Timestamp()
  now.GetCurrentTime()
  receipt = scaf(
    api_port,
    "CreateReceipt",
    {
      "vendor": "Test Vendor",
      "date": {"seconds": now.seconds, "nanos": now.nanos},
      "timezone": "UTC",
      "total": 12.34,
      "allocations": [],
      "ref": "TEST-REF",
      "notes": "Test receipt",
      "hash": "test-hash",
    },
    token=token,
  )
  assert "guid" in receipt
  assert receipt["vendor"] == "Test Vendor"
  assert receipt["total"] == 12.34
  receipt_guid = receipt["guid"]

  # Unallocated receipts should include the receipt we just created
  unallocated_response = scaf(api_port, "ListUnallocatedReceipts", {}, token=token)
  assert len(unallocated_response) > 0
  unallocated_receipts = unallocated_response["receipts"]
  our_receipt = next((r for r in unallocated_receipts if r["ref"] == "TEST-REF"), None)
  assert our_receipt is not None
  assert our_receipt["vendor"] == "Test Vendor"
  assert our_receipt["total"] == 12.34
  assert len(our_receipt.get("allocations", [])) == 0  # Should have no allocations
  assert our_receipt["guid"] == receipt_guid

  # Test: List buckets
  buckets_response = scaf(api_port, "ListBuckets", {}, token=token)
  buckets = buckets_response.get("buckets", [])
  assert len(buckets) >= 1
  assert any(b["bucket"]["guid"] == bucket_guid for b in buckets)

  # Test: Delete bucket
  delete_response = scaf(
    api_port,
    "DeleteBucket",
    {"guid": bucket_guid},
    token=token,
  )
  assert delete_response.get("success") is True

  # Verify bucket is deleted
  buckets_response = scaf(api_port, "ListBuckets", {}, token=token)
  buckets = buckets_response.get("buckets", [])
  assert not any(b["bucket"]["guid"] == bucket_guid for b in buckets)
