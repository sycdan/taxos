import json
import shutil
import sys
from datetime import datetime, timezone
from urllib.request import Request, urlopen

from google.protobuf.timestamp_pb2 import Timestamp
from taxos.access.token.generate.command import GenerateAccessToken
from taxos.access.token.revoke.command import RevokeToken
from taxos.tenant.create.command import CreateTenant
from taxos.tenant.delete.command import DeleteTenant
from taxos.tenant.entity import TenantRef

from backend.taxos import DATA_DIR, ROOT_DIR
from dev.test_api.command import TestApi


def call_connect(port: int, method: str, payload: dict, token: str = ""):
  url = f"http://localhost:{port}/taxos.v1.TaxosApi/{method}"
  data = json.dumps(payload).encode("utf-8")
  headers = {"Content-Type": "application/json"}
  if token:
    headers["Authorization"] = f"Bearer {token}"
  request = Request(url, data=data, headers=headers)
  with urlopen(request, timeout=10) as response:
    return json.loads(response.read().decode("utf-8"))


def test(port: int, token: str):
  print("\nCreating a bucket...")
  bucket = call_connect(
    port,
    "CreateBucket",
    {"name": f"Test Bucket {datetime.now().isoformat()}"},
    token=token,
  )
  print(f"✓ Created bucket: {bucket['guid']} - {bucket['name']}")
  bucket_guid = bucket["guid"]

  print("\nUpdating bucket name...")
  updated_bucket = call_connect(
    port,
    "UpdateBucket",
    {"guid": bucket_guid, "name": f"Updated Test Bucket {datetime.now().isoformat()}"},
    token=token,
  )
  print(f"✓ Updated bucket: {updated_bucket['guid']} - {updated_bucket['name']}")

  print("\nCreating a receipt...")
  now = Timestamp()
  now.GetCurrentTime()
  receipt = call_connect(
    port,
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
  print(f"✓ Created receipt: {receipt['guid']} - {receipt['vendor']}")

  print("\nListing buckets...")
  buckets_response = call_connect(port, "ListBuckets", {}, token=token)
  buckets = buckets_response.get("buckets", [])
  print(f"✓ Found {len(buckets)} buckets")
  for bucket_summary in buckets:
    bucket_info = bucket_summary.get("bucket", {})
    print(
      f"  - {bucket_info.get('name')} (${bucket_summary.get('total_amount', 0):.2f}, {bucket_summary.get('receipt_count', 0)} receipts)"
    )

  print("\nDeleting bucket...")
  delete_response = call_connect(
    port,
    "DeleteBucket",
    {"guid": bucket_guid},
    token=token,
  )
  print(f"✓ Deleted bucket: {delete_response.get('success')}")

  print("\n🎉 All tests passed!")


def handle(command: TestApi):
  sys.path.insert(0, ROOT_DIR.as_posix() + "/api")
  if command.nuke_data:
    print("💣  Nuking all data...")
    shutil.rmtree(DATA_DIR, ignore_errors=True)
    print("✓ All data nuked.")

  print(f"Testing ConnectRPC server at localhost:{command.port}...")

  # Create tenant and generate access token
  print("Creating test tenant...")
  tenant = CreateTenant(name="Test Tenant").execute()
  print(f"✓ Created tenant: {tenant.guid}")

  print("\nGenerating access token...")
  tenant_ref = TenantRef(tenant.guid.hex)
  access_token = GenerateAccessToken(tenant=tenant_ref).execute()
  print(f"✓ Generated access token: {access_token.key}")
  try:
    print("\nStarting API tests...")
    test(command.port, access_token.key)
  finally:
    RevokeToken(hash=access_token.key).execute()
    DeleteTenant(ref=tenant_ref).execute()
