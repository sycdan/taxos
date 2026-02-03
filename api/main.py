import logging
import time
from concurrent import futures

import grpc
from gen.v1 import taxos_service_pb2, taxos_service_pb2_grpc
from google.protobuf import timestamp_pb2
from taxos.bucket.create.command import CreateBucket
from taxos.bucket.load.query import LoadBucket


class TaxosApiServicer(taxos_service_pb2_grpc.TaxosApiServicer):
  def CreateBucket(self, request, context):
    logging.info(f"CreateBucket called with: {request}")
    bucket = CreateBucket(request.name).execute()
    return taxos_service_pb2.Bucket(
      guid=str(bucket.guid),
      name=bucket.name,
    )

  def GetBucket(self, request, context):
    logging.info(f"GetBucket called with guid: {request.guid}")
    return taxos_service_pb2.Bucket(
      
    )

  def ListBuckets(self, request, context):
    logging.info("ListBuckets called")
    return None

  def UpdateBucket(self, request, context):
    logging.info(f"UpdateBucket called for {request.guid}")
    return None

  def DeleteBucket(self, request, context):
    logging.info(f"DeleteBucket called for {request.guid}")
    return None

  def GetDashboard(self, request, context):
    logging.info("GetDashboard called")
    return None

  def IngestReceipt(self, request, context):
    logging.info(f"IngestReceipt called for bucket {request.bucket_guid}")
    return None


def serve():
  server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
  taxos_service_pb2_grpc.add_TaxosApiServicer_to_server(TaxosApiServicer(), server)
  server.add_insecure_port("[::]:50051")
  logging.info("Starting gRPC server on port 50051...")
  server.start()
  try:
    while True:
      time.sleep(86400)
  except KeyboardInterrupt:
    server.stop(0)


if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO)
  serve()
