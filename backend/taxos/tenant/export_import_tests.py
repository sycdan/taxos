"""Tests for tenant export and import commands."""
import json
from unittest.mock import patch

import pytest


def _make_tenant(tmp_path, name):
  from taxos.tenant.create.command import CreateTenant
  with patch("taxos.tenant.tools.TENANTS_DIR", tmp_path):
    return CreateTenant(name=name).execute()


def _del_tenant(tmp_path, tenant):
  from taxos.tenant.delete.command import DeleteTenant
  with patch("taxos.tenant.tools.TENANTS_DIR", tmp_path):
    DeleteTenant(tenant=tenant).execute()


def _set(tenant):
  from taxos.context.entity import Context
  from taxos.context.tools import set_context
  set_context(Context(tenant=tenant))


def _seed(bucket_name, vendor, total, date="2024-06-01T10:00:00"):
  from taxos.allocation.entity import Allocation
  from taxos.bucket.create.command import CreateBucket
  from taxos.bucket.entity import BucketRef
  from taxos.receipt.create.command import CreateReceipt

  bucket = CreateBucket(name=bucket_name).execute()
  allocs = {Allocation(BucketRef(bucket.guid.hex), total)}
  CreateReceipt(vendor=vendor, total=total, date=date, timezone="UTC", allocations=allocs).execute()
  return bucket


@pytest.mark.integration
class TestExportImport:
  def test_export_returns_all_entities(self, tmp_path):
    from taxos.tenant.export.command import ExportTenant

    tenant = _make_tenant(tmp_path, "Export Test")
    _set(tenant)
    _seed("Travel", "Airline", 500.0)

    data = ExportTenant().execute()

    assert len(data["buckets"]) == 1
    assert data["buckets"][0]["name"] == "Travel"
    assert len(data["vendors"]) == 1
    assert data["vendors"][0]["name"] == "Airline"
    assert len(data["receipts"]) == 1
    r = data["receipts"][0]
    assert r["vendor"] == "Airline"
    assert r["total"] == 500.0
    assert len(r["allocations"]) == 1
    assert r["allocations"][0]["amount"] == 500.0

    _del_tenant(tmp_path, tenant)

  def test_export_writes_file(self, tmp_path):
    from taxos.tenant.export.command import ExportTenant

    tenant = _make_tenant(tmp_path, "File Export Test")
    _set(tenant)

    out_file = tmp_path / "export.json"
    ExportTenant(path=str(out_file)).execute()

    assert out_file.exists()
    data = json.loads(out_file.read_text())
    assert "buckets" in data and "vendors" in data and "receipts" in data

    _del_tenant(tmp_path, tenant)

  def test_import_from_export_roundtrip(self, tmp_path):
    from taxos import db
    from taxos.tenant.export.command import ExportTenant
    from taxos.tenant.import_.command import ImportTenant

    src = _make_tenant(tmp_path, "Source Tenant")
    _set(src)
    _seed("Office", "Staples", 45.0, "2024-03-01T09:00:00")

    export_file = tmp_path / "export.json"
    ExportTenant(path=str(export_file)).execute()

    dst = _make_tenant(tmp_path, "Dest Tenant")
    _set(dst)
    counts = ImportTenant(source=str(export_file)).execute()

    assert counts == {"buckets": 1, "vendors": 1, "receipts": 1}

    buckets = db.query("MATCH (b:Bucket) RETURN b.name AS name", database=dst.db_name)
    assert buckets[0]["name"] == "Office"

    rows = db.query(
      "MATCH (r:Receipt) OPTIONAL MATCH (r)-[a:ALLOCATED_TO]->(b) RETURN r.vendor AS vendor, collect(a.amount) AS amounts",
      database=dst.db_name,
    )
    assert rows[0]["vendor"] == "Staples"
    assert rows[0]["amounts"] == [45.0]

    _del_tenant(tmp_path, src)
    _del_tenant(tmp_path, dst)

  def test_import_from_flat_dir(self, tmp_path):
    """Import from old flat-file tenant directory structure."""
    from taxos import db
    from taxos.tenant.import_.command import ImportTenant

    bucket_guid = "11111111-1111-1111-1111-111111111111"
    receipt_guid = "22222222-2222-2222-2222-222222222222"
    vendor_guid = "33333333-3333-3333-3333-333333333333"

    flat_dir = tmp_path / "flat_tenant"
    (flat_dir / "buckets" / bucket_guid.replace("-", "")).mkdir(parents=True)
    (flat_dir / "vendors" / vendor_guid.replace("-", "")).mkdir(parents=True)
    (flat_dir / "receipts" / receipt_guid.replace("-", "")).mkdir(parents=True)

    (flat_dir / "buckets" / bucket_guid.replace("-", "") / "state.json").write_text(
      json.dumps({"guid": bucket_guid, "name": "Food"})
    )
    (flat_dir / "vendors" / vendor_guid.replace("-", "") / "state.json").write_text(
      json.dumps({"guid": vendor_guid, "name": "Grocery Store"})
    )
    (flat_dir / "receipts" / receipt_guid.replace("-", "") / "state.json").write_text(
      json.dumps({
        "guid": receipt_guid,
        "vendor": "Grocery Store",
        "total": 120.0,
        "date": "2024-05-10T14:00:00",
        "timezone": "UTC",
        "allocations": [{"bucket": bucket_guid, "amount": 120.0}],
        "vendor_ref": "",
        "notes": "weekly shop",
        "hash": "",
      })
    )

    tenant = _make_tenant(tmp_path, "Import Flat Test")
    _set(tenant)
    counts = ImportTenant(source=str(flat_dir)).execute()

    assert counts == {"buckets": 1, "vendors": 1, "receipts": 1}

    rows = db.query(
      "MATCH (r:Receipt) RETURN r.vendor AS vendor, r.total AS total, r.notes AS notes",
      database=tenant.db_name,
    )
    assert rows[0]["vendor"] == "Grocery Store"
    assert rows[0]["total"] == 120.0
    assert rows[0]["notes"] == "weekly shop"

    _del_tenant(tmp_path, tenant)
