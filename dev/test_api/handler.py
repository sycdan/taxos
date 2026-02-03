import sys
from datetime import datetime, timezone

import grpc
from google.protobuf.timestamp_pb2 import Timestamp
from taxos import ROOT_DIR

from dev.test_api.command import TestApi


def get_stub(port: int):
  from api.v1.taxos_service_pb2_grpc import TaxosApiStub

  target = f"localhost:{port}"
  channel = grpc.insecure_channel(target)
  print(f"Connecting to gRPC server at {target}...")
  return TaxosApiStub(channel)


def test(stub):
  import api.v1.taxos_service_pb2 as api

  print("\nCreating a bucket...")
  create_request = api.CreateBucketRequest(name="Test Bucket")
  bucket = stub.CreateBucket(create_request)
  print(f"✓ Created bucket: {bucket.guid} - {bucket.name}")
  bucket_guid = bucket.guid

  print("\n2. Getting the bucket...")
  get_request = api.GetBucketRequest(guid=bucket_guid)
  retrieved_bucket = stub.GetBucket(get_request)
  print(f"✓ Retrieved bucket: {retrieved_bucket.guid} - {retrieved_bucket.name}")

  #   # Test 3: Update the bucket
  #   print("\n3. Updating the bucket...")
  #   update_request = pb.UpdateBucketRequest(
  #     guid=bucket_guid, name="Updated Test Bucket"
  #   )
  #   updated_bucket = stub.UpdateBucket(update_request)
  #   print(f"✓ Updated bucket: {updated_bucket.guid} - {updated_bucket.name}")

  #   # Test 4: List buckets
  #   print("\n4. Listing buckets...")
  #   now = Timestamp()
  #   now.GetCurrentTime()

  #   # List buckets from last month to now
  #   start_time = Timestamp()
  #   start_time.FromDatetime(datetime.now(timezone.utc).replace(day=1))

  #   list_request = pb.ListBucketsRequest(
  #     start_date=start_time, end_date=now, include_empty=True
  #   )
  #   buckets_response = stub.ListBuckets(list_request)
  #   print(f"✓ Found {len(buckets_response.buckets)} buckets")
  #   for bucket_summary in buckets_response.buckets:
  #     print(
  #       f"  - {bucket_summary.bucket.name} (${bucket_summary.total_amount:.2f}, {bucket_summary.receipt_count} receipts)"
  #     )

  #   # Test 5: Get dashboard
  #   print("\n5. Getting dashboard...")
  #   dashboard_request = pb.GetDashboardRequest(
  #     start_date=start_time, end_date=now, include_empty_buckets=True
  #   )
  #   dashboard = stub.GetDashboard(dashboard_request)
  #   print(
  #     f"✓ Dashboard: ${dashboard.total_amount:.2f} total, {dashboard.total_receipts} receipts"
  #   )

  #   # Test 6: Ingest a receipt (optional - only if you want to test file upload)
  #   # print("\n6. Ingesting a test receipt...")
  #   # receipt_request = pb.IngestReceiptRequest(
  #   #   bucket_guid=bucket_guid,
  #   #   content=b"fake receipt content",
  #   #   filename="test_receipt.txt"
  #   # )
  #   # receipt = stub.IngestReceipt(receipt_request)
  #   # print(f"✓ Ingested receipt: {receipt.guid} - {receipt.description}")

  #   # Test 7: Delete the bucket (cleanup)
  #   print("\n7. Cleaning up - deleting test bucket...")
  #   delete_request = pb.DeleteBucketRequest(guid=bucket_guid)
  #   delete_response = stub.DeleteBucket(delete_request)
  #   print(f"✓ Deleted bucket: {delete_response.success}")

  #   print("\n🎉 All tests passed!")


def handle(command: TestApi):
  if command.use_proxy:
    port = 8080
  else:
    port = 50051

  sys.path.insert(0, ROOT_DIR.as_posix() + "/api")
  stub = get_stub(port)

  test(stub)
