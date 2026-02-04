import json
import logging

from flask import Flask, Response, request
from flask_cors import CORS
from google.protobuf.json_format import MessageToDict, Parse
from taxos.bucket.create.command import CreateBucket
from taxos.bucket.delete.command import DeleteBucket
from taxos.bucket.entity import BucketRef
from taxos.bucket.load.query import LoadBucket
from taxos.bucket.update.command import UpdateBucket
from taxos.list_buckets.query import ListBuckets

from api.v1 import taxos_service_pb2 as models

logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)


@app.route("/taxos.v1.TaxosApi/ListBuckets", methods=["POST"])
def list_buckets():
  logger.info("ListBuckets called via ConnectRPC")
  try:
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

    response = models.ListBucketsResponse(buckets=buckets)
    response_dict = MessageToDict(response, preserving_proto_field_name=True)

    logger.info(f"Returning {len(buckets)} buckets")
    return Response(json.dumps(response_dict), content_type="application/json")
  except Exception as e:
    logger.error(f"Failed to list buckets: {e}")
    return Response(json.dumps({"error": str(e)}), status=500, content_type="application/json")


@app.route("/taxos.v1.TaxosApi/CreateBucket", methods=["POST"])
def create_bucket():
  logger.info("CreateBucket called via ConnectRPC")
  try:
    request_data = request.get_json()
    bucket = CreateBucket(request_data.get("name", "")).execute()

    response = models.Bucket(
      guid=str(bucket.guid),
      name=bucket.name,
    )
    response_dict = MessageToDict(response, preserving_proto_field_name=True)

    return Response(json.dumps(response_dict), content_type="application/json")
  except Exception as e:
    logger.error(f"Failed to create bucket: {e}")
    return Response(json.dumps({"error": str(e)}), status=500, content_type="application/json")


@app.route("/taxos.v1.TaxosApi/GetBucket", methods=["POST"])
def get_bucket():
  logger.info("GetBucket called via ConnectRPC")
  try:
    request_data = request.get_json()
    bucket_ref = BucketRef(guid=request_data.get("guid", ""))
    bucket = LoadBucket(ref=bucket_ref).execute()

    response = models.Bucket(
      guid=str(bucket.guid),
      name=bucket.name,
    )
    response_dict = MessageToDict(response, preserving_proto_field_name=True)

    return Response(json.dumps(response_dict), content_type="application/json")
  except Exception as e:
    logger.error(f"Failed to get bucket: {e}")
    return Response(json.dumps({"error": str(e)}), status=404, content_type="application/json")


if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO)
  logger.info("Starting ConnectRPC HTTP server on port 50051...")
  app.run(host="0.0.0.0", port=50051, debug=True)
