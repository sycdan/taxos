import asyncio
import json
import sqlite3
import uuid
from concurrent import futures
from datetime import datetime
from typing import List, Optional

import grpc

# Import the generated gRPC code
import taxos_service_pb2
import taxos_service_pb2_grpc


class TaxosServicer(taxos_service_pb2_grpc.TaxosServiceServicer):
  def __init__(self, db_path: str = "taxos.db"):
    self.db_path = db_path
    self._init_db()

  def _init_db(self):
    """Initialize the SQLite database with required tables."""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()

    # Create buckets table
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS buckets (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            )
        """)

    # Create receipts table
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS receipts (
                id TEXT PRIMARY KEY,
                bucket_id TEXT NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                date INTEGER NOT NULL,
                image_url TEXT,
                metadata TEXT,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL,
                FOREIGN KEY (bucket_id) REFERENCES buckets (id)
            )
        """)

    conn.commit()
    conn.close()

  def _get_connection(self):
    return sqlite3.connect(self.db_path)

  def _timestamp_now(self):
    return int(datetime.now().timestamp() * 1000)

  async def CreateBucket(self, request, context):
    """Create a new bucket."""
    bucket_id = str(uuid.uuid4())
    now = self._timestamp_now()

    conn = self._get_connection()
    cursor = conn.cursor()

    try:
      cursor.execute(
        """
                INSERT INTO buckets (id, name, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """,
        (bucket_id, request.name, request.description, now, now),
      )
      conn.commit()

      return taxos_service_pb2.Bucket(
        id=bucket_id,
        name=request.name,
        description=request.description,
        created_at=now,
        updated_at=now,
      )
    except Exception as e:
      context.set_code(grpc.StatusCode.INTERNAL)
      context.set_details(str(e))
      return taxos_service_pb2.Bucket()
    finally:
      conn.close()

  async def GetBucket(self, request, context):
    """Get a bucket by ID."""
    conn = self._get_connection()
    cursor = conn.cursor()

    try:
      cursor.execute("SELECT * FROM buckets WHERE id = ?", (request.id,))
      row = cursor.fetchone()

      if not row:
        context.set_code(grpc.StatusCode.NOT_FOUND)
        context.set_details("Bucket not found")
        return taxos_service_pb2.Bucket()

      return taxos_service_pb2.Bucket(
        id=row[0], name=row[1], description=row[2] or "", created_at=row[3], updated_at=row[4]
      )
    except Exception as e:
      context.set_code(grpc.StatusCode.INTERNAL)
      context.set_details(str(e))
      return taxos_service_pb2.Bucket()
    finally:
      conn.close()

  async def ListBuckets(self, request, context):
    """List all buckets with their summaries."""
    conn = self._get_connection()
    cursor = conn.cursor()

    try:
      # Build the query based on filters
      base_query = """
                SELECT b.*, 
                       COALESCE(SUM(r.amount), 0) as total_amount,
                       COUNT(r.id) as receipt_count
                FROM buckets b
                LEFT JOIN receipts r ON b.id = r.bucket_id
            """

      params = []
      where_conditions = []

      if request.start_date > 0:
        where_conditions.append("(r.date IS NULL OR r.date >= ?)")
        params.append(request.start_date)

      if request.end_date > 0:
        where_conditions.append("(r.date IS NULL OR r.date <= ?)")
        params.append(request.end_date)

      if where_conditions:
        base_query += " WHERE " + " AND ".join(where_conditions)

      base_query += " GROUP BY b.id ORDER BY b.name"

      cursor.execute(base_query, params)
      rows = cursor.fetchall()

      bucket_summaries = []
      for row in rows:
        total_amount = row[5]
        receipt_count = row[6]

        # Skip empty buckets if requested
        if not request.include_empty and receipt_count == 0:
          continue

        bucket = taxos_service_pb2.Bucket(
          id=row[0], name=row[1], description=row[2] or "", created_at=row[3], updated_at=row[4]
        )

        bucket_summary = taxos_service_pb2.BucketSummary(
          bucket=bucket, total_amount=total_amount, receipt_count=receipt_count
        )
        bucket_summaries.append(bucket_summary)

      return taxos_service_pb2.ListBucketsResponse(buckets=bucket_summaries)
    except Exception as e:
      context.set_code(grpc.StatusCode.INTERNAL)
      context.set_details(str(e))
      return taxos_service_pb2.ListBucketsResponse()
    finally:
      conn.close()

  async def CreateReceipt(self, request, context):
    """Create a new receipt."""
    receipt_id = str(uuid.uuid4())
    now = self._timestamp_now()

    conn = self._get_connection()
    cursor = conn.cursor()

    try:
      # Verify bucket exists
      cursor.execute("SELECT id FROM buckets WHERE id = ?", (request.bucket_id,))
      if not cursor.fetchone():
        context.set_code(grpc.StatusCode.NOT_FOUND)
        context.set_details("Bucket not found")
        return taxos_service_pb2.Receipt()

      # Convert metadata to JSON string
      import json

      metadata_json = json.dumps(dict(request.metadata))

      cursor.execute(
        """
                INSERT INTO receipts (id, bucket_id, description, amount, date, image_url, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
        (
          receipt_id,
          request.bucket_id,
          request.description,
          request.amount,
          request.date,
          request.image_url,
          metadata_json,
          now,
          now,
        ),
      )
      conn.commit()

      return taxos_service_pb2.Receipt(
        id=receipt_id,
        bucket_id=request.bucket_id,
        description=request.description,
        amount=request.amount,
        date=request.date,
        image_url=request.image_url,
        metadata=request.metadata,
        created_at=now,
        updated_at=now,
      )
    except Exception as e:
      context.set_code(grpc.StatusCode.INTERNAL)
      context.set_details(str(e))
      return taxos_service_pb2.Receipt()
    finally:
      conn.close()

  async def ListReceipts(self, request, context):
    """List receipts for a bucket."""
    conn = self._get_connection()
    cursor = conn.cursor()

    try:
      # Build query with filters
      base_query = "SELECT * FROM receipts WHERE bucket_id = ?"
      params = [request.bucket_id]

      if request.start_date > 0:
        base_query += " AND date >= ?"
        params.append(request.start_date)

      if request.end_date > 0:
        base_query += " AND date <= ?"
        params.append(request.end_date)

      base_query += " ORDER BY date DESC"

      if request.limit > 0:
        base_query += " LIMIT ?"
        params.append(request.limit)

        if request.offset > 0:
          base_query += " OFFSET ?"
          params.append(request.offset)

      cursor.execute(base_query, params)
      rows = cursor.fetchall()

      # Get total count
      count_query = "SELECT COUNT(*) FROM receipts WHERE bucket_id = ?"
      count_params = [request.bucket_id]
      if request.start_date > 0:
        count_query += " AND date >= ?"
        count_params.append(request.start_date)
      if request.end_date > 0:
        count_query += " AND date <= ?"
        count_params.append(request.end_date)

      cursor.execute(count_query, count_params)
      total_count = cursor.fetchone()[0]

      receipts = []
      for row in rows:
        import json

        metadata = json.loads(row[6]) if row[6] else {}

        receipt = taxos_service_pb2.Receipt(
          id=row[0],
          bucket_id=row[1],
          description=row[2],
          amount=row[3],
          date=row[4],
          image_url=row[5] or "",
          metadata=metadata,
          created_at=row[7],
          updated_at=row[8],
        )
        receipts.append(receipt)

      return taxos_service_pb2.ListReceiptsResponse(receipts=receipts, total_count=total_count)
    except Exception as e:
      context.set_code(grpc.StatusCode.INTERNAL)
      context.set_details(str(e))
      return taxos_service_pb2.ListReceiptsResponse()
    finally:
      conn.close()

  async def GetDashboard(self, request, context):
    """Get dashboard summary."""
    conn = self._get_connection()
    cursor = conn.cursor()

    try:
      # Get bucket summaries (reuse ListBuckets logic)
      list_request = taxos_service_pb2.ListBucketsRequest(
        start_date=request.start_date,
        end_date=request.end_date,
        include_empty=request.include_empty_buckets,
      )
      buckets_response = await self.ListBuckets(list_request, context)

      # Calculate totals
      total_amount = sum(b.total_amount for b in buckets_response.buckets)
      total_receipts = sum(b.receipt_count for b in buckets_response.buckets)

      return taxos_service_pb2.DashboardResponse(
        bucket_summaries=buckets_response.buckets,
        total_amount=total_amount,
        total_receipts=total_receipts,
      )
    except Exception as e:
      context.set_code(grpc.StatusCode.INTERNAL)
      context.set_details(str(e))
      return taxos_service_pb2.DashboardResponse()
    finally:
      conn.close()


async def serve():
  server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
  taxos_service_pb2_grpc.add_TaxosServiceServicer_to_server(TaxosServicer(), server)

  listen_addr = "[::]:50051"
  server.add_insecure_port(listen_addr)

  print(f"Starting Taxos gRPC server on {listen_addr}")
  await server.start()
  await server.wait_for_termination()


if __name__ == "__main__":
  asyncio.run(serve())
