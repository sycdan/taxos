import logging

from taxos import db
from taxos.context.tools import require_tenant
from taxos.receipt.entity import Receipt
from taxos.receipt.load.handler import _read_file_attachments
from taxos.tenant.dashboard.entity import BucketSummary, Dashboard
from taxos.tenant.dashboard.get.query import GetDashboard
from taxos.vendor.list.query import ListVendors
from taxos.vendor.entity import Vendor

logger = logging.getLogger(__name__)


def handle(query: GetDashboard) -> Dashboard:
  logger.info(f"Generating dashboard for months: {query.months}")
  tenant = require_tenant()

  # Bucket totals in selected months
  bucket_where = (
    "WHERE any(m IN $months WHERE r.date STARTS WITH m)" if query.months else ""
  )

  bucket_records = db.query(
    f"""
    MATCH (b:Bucket)
    OPTIONAL MATCH (b)<-[a:ALLOCATED_TO]-(r:Receipt)
    {bucket_where}
    WITH b, sum(a.amount) AS total, count(DISTINCT r) AS receipt_count
    RETURN b.guid AS guid, b.name AS name, total, receipt_count
    ORDER BY b.name
    """,
    {"months": query.months},
    database=tenant.db_name,
  )

  bucket_summaries = [
    BucketSummary(
      guid=row["guid"],
      name=row["name"],
      total_amount=row["total"] or 0.0,
      receipt_count=row["receipt_count"] or 0,
    )
    for row in bucket_records
  ]

  unallocated_where_parts = ["NOT (r)-[:ALLOCATED_TO]->()"]
  if query.months:
    unallocated_where_parts.append("any(m IN $months WHERE r.date STARTS WITH m)")
  unallocated_where = "WHERE " + " AND ".join(unallocated_where_parts)

  unallocated_records = db.query(
    f"""
    MATCH (r:Receipt)
    {unallocated_where}
    OPTIONAL MATCH (r)-[:FROM_VENDOR]->(v:Vendor)
    OPTIONAL MATCH (vf:Vendor {{name_lower: toLower(r.vendor)}})
    RETURN
      r,
      coalesce(v.guid, vf.guid) AS vendor_guid,
      coalesce(v.name, vf.name, r.vendor) AS vendor_name
    """,
    {"months": query.months},
    database=tenant.db_name,
  )

  unallocated_receipts = [
    Receipt(
      guid=row["r"]["guid"],
      vendor=Vendor(row["vendor_guid"], row["vendor_name"]),
      total=row["r"]["total"],
      date=row["r"]["date"],
      timezone=row["r"]["timezone"],
      notes=row["r"].get("notes", ""),
      file_attachments=_read_file_attachments(row["r"]),
      reference=row["r"].get("reference", ""),
    )
    for row in unallocated_records
  ]

  vendors = ListVendors().execute()

  return Dashboard(
    buckets=bucket_summaries,
    unallocated=unallocated_receipts,
    vendor_names=[v.name for v in vendors],
  )
