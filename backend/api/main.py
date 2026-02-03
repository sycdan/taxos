import logging
import time
from concurrent import futures

import grpc
from google.protobuf import timestamp_pb2
from taxos.bucket.create.command import CreateBucket
from taxos.bucket.load.query import LoadBucket
from taxos.list_buckets.query import ListBuckets

from api.v1 import taxos_service_pb2 as models
from api.v1 import taxos_service_pb2_grpc

logger = logging.getLogger("api")


class TaxosApiServicer(taxos_service_pb2_grpc.TaxosApiServicer):
  def CreateBucket(self, request, context):
    logger.info(f"CreateBucket called with: {request}")
    bucket = CreateBucket(request.name).execute()
    return models.Bucket(
      guid=str(bucket.guid),
      name=bucket.name,
    )

  def GetBucket(self, request, context):
    logger.info(f"GetBucket called with guid: {request.guid}")
    return None

  def ListBuckets(self, request, context):
    logger.info("ListBuckets called")
    repo = ListBuckets().execute()
    buckets = [
      models.BucketSummary(
        bucket=models.Bucket(
          guid=str(bucket.guid),
          name=bucket.name,
        )
      )
      for bucket in repo.index.values()
    ]
    logger.info(f"Listing {len(buckets)} buckets")
    for bucket_summary in buckets:
      logger.info(f"  - {bucket_summary.bucket.name}")
    return models.ListBucketsResponse(buckets=buckets)

  def UpdateBucket(self, request, context):
    logger.info(f"UpdateBucket called for {request.guid}")
    return None

  def DeleteBucket(self, request, context):
    logger.info(f"DeleteBucket called for {request.guid}")
    return None

  def GetDashboard(self, request, context):
    logger.info("GetDashboard called")
    return None

  def IngestReceipt(self, request, context):
    logger.info(f"IngestReceipt called for bucket {request.bucket_guid}")
    return None


def serve():
  server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
  taxos_service_pb2_grpc.add_TaxosApiServicer_to_server(TaxosApiServicer(), server)
  server.add_insecure_port("[::]:50051")
  logger.info("Starting gRPC server on port 50051...")
  server.start()
  try:
    while True:
      time.sleep(86400)
  except KeyboardInterrupt:
    server.stop(0)


if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO)
  serve()
