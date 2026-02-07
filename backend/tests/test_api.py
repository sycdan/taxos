import json
from datetime import datetime
from urllib.request import Request, urlopen

import pytest
from google.protobuf.timestamp_pb2 import Timestamp
from taxos.access.token.generate.command import GenerateAccessToken
from taxos.access.token.revoke.command import RevokeToken
from taxos.tenant.create.command import CreateTenant
from taxos.tenant.delete.command import DeleteTenant
from taxos.tenant.entity import TenantRef


@pytest.fixture
def api_port():
  """Port where the ConnectRPC API server is running"""
  return 50051


@pytest.fixture
def test_tenant():
  """Create a test tenant and generate access token, cleanup after test"""
  # Create tenant
  tenant = CreateTenant(name="Test Tenant").execute()
  tenant_ref = TenantRef(tenant.guid.hex)

  # Generate access token
  access_token = GenerateAccessToken(tenant=tenant_ref).execute()

  yield {"tenant": tenant, "tenant_ref": tenant_ref, "token": access_token.key}

  # Cleanup
  try:
    RevokeToken(hash=access_token.key).execute()
    DeleteTenant(ref=tenant_ref).execute()
  except Exception as e:
    print(f"Cleanup warning: {e}")


def call_api(port: int, method: str, payload: dict, token: str = "", timeout: int = 30):
  """Make a ConnectRPC API call"""
  url = f"http://localhost:{port}/taxos.v1.TaxosApi/{method}"
  data = json.dumps(payload).encode("utf-8")
  headers = {"Content-Type": "application/json"}
  if token:
    headers["Authorization"] = f"Bearer {token}"
  request = Request(url, data=data, headers=headers)
  with urlopen(request, timeout=timeout) as response:
    return json.loads(response.read().decode("utf-8"))


@pytest.mark.integration
def test_api_integration(api_port, test_tenant):
  """Full API integration test including tenant authentication"""
  token = test_tenant["token"]

  # Test: Create bucket
  bucket = call_api(
    api_port,
    "CreateBucket",
    {"name": f"Test Bucket {datetime.now().isoformat()}"},
    token=token,
  )
  assert "guid" in bucket
  assert "name" in bucket
  bucket_guid = bucket["guid"]

  # Test: Update bucket
  updated_bucket = call_api(
    api_port,
    "UpdateBucket",
    {"guid": bucket_guid, "name": f"Updated Test Bucket {datetime.now().isoformat()}"},
    token=token,
  )
  assert updated_bucket["guid"] == bucket_guid
  assert "Updated" in updated_bucket["name"]

  # Test: Create receipt
  now = Timestamp()
  now.GetCurrentTime()
  receipt = call_api(
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
  unallocated_response = call_api(api_port, "ListUnallocatedReceipts", {}, token=token)
  assert "receipts" in unallocated_response
  unallocated_receipts = unallocated_response["receipts"]
  our_receipt = next((r for r in unallocated_receipts if r["ref"] == "TEST-REF"), None)
  assert our_receipt is not None
  assert our_receipt["vendor"] == "Test Vendor"
  assert our_receipt["total"] == 12.34
  assert len(our_receipt.get("allocations", [])) == 0  # Should have no allocations
  assert our_receipt["guid"] == receipt_guid

  # Test: List buckets
  buckets_response = call_api(api_port, "ListBuckets", {}, token=token)
  buckets = buckets_response.get("buckets", [])
  assert len(buckets) >= 1
  assert any(b["bucket"]["guid"] == bucket_guid for b in buckets)

  # Test: Delete bucket
  delete_response = call_api(
    api_port,
    "DeleteBucket",
    {"guid": bucket_guid},
    token=token,
  )
  assert delete_response.get("success") is True

  # Verify bucket is deleted
  buckets_response = call_api(api_port, "ListBuckets", {}, token=token)
  buckets = buckets_response.get("buckets", [])
  assert not any(b["bucket"]["guid"] == bucket_guid for b in buckets)


@pytest.mark.integration
def test_api_authentication(api_port):
  """Test that API properly rejects requests without valid token"""
  from urllib.error import HTTPError

  # Should fail without token
  with pytest.raises(HTTPError) as exc_info:
    call_api(api_port, "ListBuckets", {})
  assert exc_info.value.code == 401

  # Should fail with invalid token
  with pytest.raises(HTTPError) as exc_info:
    call_api(api_port, "ListBuckets", {}, token="invalid-token")
  assert exc_info.value.code == 401
