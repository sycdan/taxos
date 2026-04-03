from unittest.mock import patch
from uuid import UUID
import pytest

from taxos.tenant.entity import Tenant


def _neo4j_db_exists(db_name: str) -> bool:
  from taxos import db

  records = db.query(
    "SHOW DATABASES YIELD name WHERE name = $name RETURN name",
    {"name": db_name},
    database="system",
  )
  return len(records) > 0


# ---------------------------------------------------------------------------
# entity
# ---------------------------------------------------------------------------


class TestTenantDbName:
  def test_db_name_prefix(self):
    tenant = Tenant(guid=UUID("01930000-0000-7000-8000-000000000001"), name="test")
    assert tenant.db_name.startswith("t")

  def test_db_name_is_hex(self):
    tenant = Tenant(guid=UUID("01930000-0000-7000-8000-000000000001"), name="test")
    hex_part = tenant.db_name[1:]
    assert all(c in "0123456789abcdef" for c in hex_part)

  def test_db_name_matches_guid_hex(self):
    guid = UUID("01930000-0000-7000-8000-000000000001")
    tenant = Tenant(guid=guid, name="test")
    assert tenant.db_name == f"t{guid.hex}"

  def test_no_state_file_attribute(self):
    tenant = Tenant(guid=UUID("01930000-0000-7000-8000-000000000001"), name="test")
    assert not hasattr(type(tenant), "state_file")


# ---------------------------------------------------------------------------
# create handler
# ---------------------------------------------------------------------------


class TestCreateTenantHandler:
  @pytest.mark.unit
  def test_creates_neo4j_database(self, tmp_path):
    from taxos.tenant.create.handler import handle
    from taxos.tenant.create.command import CreateTenant

    with (
      patch("taxos.tenant.create.handler.db") as mock_db,
      patch("taxos.tenant.tools.TENANTS_DIR", tmp_path),
    ):
      result = handle(CreateTenant(name="Acme"))

    mock_db.run.assert_called_once()
    call_args = mock_db.run.call_args
    assert "CREATE DATABASE" in call_args[0][0]
    assert call_args[1]["database"] == "system"
    assert result.db_name in call_args[0][0]

  @pytest.mark.unit
  def test_returns_tenant_with_db_name(self, tmp_path):
    from taxos.tenant.create.handler import handle
    from taxos.tenant.create.command import CreateTenant

    with (
      patch("taxos.tenant.create.handler.db"),
      patch("taxos.tenant.tools.TENANTS_DIR", tmp_path),
    ):
      result = handle(CreateTenant(name="Acme"))

    assert result.name == "Acme"
    assert result.db_name.startswith("t")


# ---------------------------------------------------------------------------
# delete handler
# ---------------------------------------------------------------------------


class TestDeleteTenantHandler:
  def _make_tenant(self, tmp_path):
    guid = UUID("01930000-0000-7000-8000-000000000001")
    tenant = Tenant(guid=guid, name="Acme")
    # create the content dir so the handler finds it
    content_dir = tmp_path / guid.hex
    content_dir.mkdir()
    return tenant, content_dir

  @pytest.mark.unit
  def test_drops_neo4j_database(self, tmp_path):
    from taxos.tenant.delete.handler import handle
    from taxos.tenant.delete.command import DeleteTenant

    tenant, _ = self._make_tenant(tmp_path)

    with (
      patch("taxos.tenant.delete.handler.db") as mock_db,
      patch("taxos.tenant.delete.handler.ACCESS_TOKENS_DIR", tmp_path / "tokens"),
      patch("taxos.tenant.tools.TENANTS_DIR", tmp_path),
      patch.object(
        type(tenant),
        "content_dir",
        new_callable=lambda: property(lambda self: tmp_path / self.guid.hex),
      ),
    ):
      result = handle(DeleteTenant(tenant=tenant))

    mock_db.run.assert_called_once()
    call_args = mock_db.run.call_args
    assert "DROP DATABASE" in call_args[0][0]
    assert "DESTROY DATA" in call_args[0][0]
    assert call_args[1]["database"] == "system"
    assert result is True

  @pytest.mark.unit
  def test_drops_database_even_when_no_content_dir(self, tmp_path):
    from taxos.tenant.delete.handler import handle
    from taxos.tenant.delete.command import DeleteTenant

    guid = UUID("01930000-0000-7000-8000-000000000002")
    tenant = Tenant(guid=guid, name="Acme")

    with (
      patch("taxos.tenant.delete.handler.db") as mock_db,
      patch("taxos.tenant.delete.handler.ACCESS_TOKENS_DIR", tmp_path / "tokens"),
      patch.object(
        type(tenant),
        "content_dir",
        new_callable=lambda: property(lambda self: tmp_path / "nonexistent"),
      ),
    ):
      result = handle(DeleteTenant(tenant=tenant))

    mock_db.run.assert_called_once()
    assert result is True


# ---------------------------------------------------------------------------
# integration
# ---------------------------------------------------------------------------


class TestTenantLifecycleIntegration:
  @pytest.mark.integration
  def test_create_and_delete_provisions_and_drops_neo4j_database(self, tmp_path):
    from taxos.tenant.create.command import CreateTenant
    from taxos.tenant.delete.command import DeleteTenant

    with patch("taxos.tenant.tools.TENANTS_DIR", tmp_path):
      tenant = CreateTenant(name="Integration Test Tenant").execute()

    assert _neo4j_db_exists(tenant.db_name), "database should exist after create"

    with patch("taxos.tenant.tools.TENANTS_DIR", tmp_path):
      DeleteTenant(tenant=tenant).execute()

    assert not _neo4j_db_exists(tenant.db_name), "database should be gone after delete"


# ---------------------------------------------------------------------------
# backup/restore
# ---------------------------------------------------------------------------


def _make_tenant_for_backup(tmp_path, name: str):
  from taxos.tenant.create.command import CreateTenant

  with patch("taxos.tenant.tools.TENANTS_DIR", tmp_path):
    return CreateTenant(name=name).execute()


def _delete_tenant_for_backup(tmp_path, tenant):
  from taxos.tenant.delete.command import DeleteTenant

  with patch("taxos.tenant.tools.TENANTS_DIR", tmp_path):
    DeleteTenant(tenant=tenant).execute()


def _set_context_tenant(tenant):
  from taxos.context.entity import Context
  from taxos.context.tools import set_context

  set_context(Context(tenant=tenant))


def _create_test_data(
  bucket_name: str,
  vendor: str,
  total: float,
  date: str = "2024-06-01T10:00:00",
  reference: str = "",
  notes: str = "",
):
  from taxos.allocation.entity import Allocation
  from taxos.bucket.create.command import CreateBucket
  from taxos.receipt.create.command import CreateReceipt

  bucket = CreateBucket(name=bucket_name).execute()
  allocs = {Allocation(bucket, total)}
  receipt = CreateReceipt(
    vendor=vendor,
    total=total,
    date=date,
    timezone="UTC",
    allocations=allocs,
    reference=reference,
    notes=notes,
  ).execute()
  return bucket, receipt


def _tenant_state(db, tenant) -> dict:
  """Return a normalized, order-stable snapshot of all tenant state."""
  buckets = sorted(
    [
      {"guid": r["guid"], "name": r["name"]}
      for r in db.query(
        "MATCH (b:Bucket) RETURN b.guid AS guid, b.name AS name",
        database=tenant.db_name,
      )
    ],
    key=lambda x: x["guid"],
  )

  vendors = sorted(
    [
      {"guid": r["guid"], "name": r["name"]}
      for r in db.query(
        "MATCH (v:Vendor) RETURN v.guid AS guid, v.name AS name",
        database=tenant.db_name,
      )
    ],
    key=lambda x: x["guid"],
  )

  receipt_rows = db.query(
    """
    MATCH (r:Receipt)
    OPTIONAL MATCH (r)-[:FROM_VENDOR]->(v:Vendor)
    OPTIONAL MATCH (r)-[a:ALLOCATED_TO]->(b:Bucket)
    RETURN
      r.guid AS guid, r.total AS total, r.date AS date,
      r.timezone AS timezone, r.reference AS reference,
      r.notes AS notes, r.hash AS hash,
      v.guid AS vendor_guid,
      collect({bucket: b.guid, amount: a.amount}) AS allocations
    """,
    database=tenant.db_name,
  )
  receipts = sorted(
    [
      {
        "guid": r["guid"],
        "total": r["total"],
        "date": r["date"],
        "timezone": r["timezone"],
        "reference": r["reference"] or "",
        "notes": r["notes"] or "",
        "hash": r["hash"] or "",
        "vendor_guid": r["vendor_guid"],
        "allocations": sorted(
          [
            {"bucket": a["bucket"], "amount": a["amount"]}
            for a in r["allocations"]
            if a["bucket"] is not None
          ],
          key=lambda a: a["bucket"],
        ),
      }
      for r in receipt_rows
    ],
    key=lambda x: x["guid"],
  )

  return {"buckets": buckets, "vendors": vendors, "receipts": receipts}


class TestBackupRestore:
  @pytest.mark.integration
  def test_backup_restore_round_trip(self, tmp_path):
    """Full round-trip: create tenant with data and a file attachment, backup, delete, restore, verify state."""
    import zipfile as zf_mod

    from taxos import db
    from taxos.receipt.attach_file.command import AttachFile
    from taxos.tenant.backup.command import BackupTenant
    from taxos.tenant.restore.command import RestoreTenant

    tenant = _make_tenant_for_backup(tmp_path, "Round Trip Test")
    _set_context_tenant(tenant)
    _, receipt = _create_test_data(
      "Office",
      "Staples",
      120.0,
      "2024-03-01T09:00:00",
      reference="INV-001",
      notes="monthly supplies",
    )

    fake_file = tmp_path / "invoice.pdf"
    fake_file.write_bytes(b"fake pdf content")
    with patch("taxos.tenant.tools.TENANTS_DIR", tmp_path):
      receipt = AttachFile(receipt_ref=receipt, filepath=fake_file).execute()
    file_hash = receipt.hash

    original_guid = tenant.guid.hex
    before = _tenant_state(db, tenant)

    with (
      patch("taxos.tenant.tools.TENANTS_DIR", tmp_path),
      patch("taxos.BACKUPS_DIR", tmp_path / "backups"),
    ):
      backup_path = BackupTenant(zip=True).execute()

    _delete_tenant_for_backup(tmp_path, tenant)

    with patch("taxos.tenant.tools.TENANTS_DIR", tmp_path):
      token = RestoreTenant(source=backup_path, name="Round Trip Test").execute()

    restored = token.tenant
    assert isinstance(restored, Tenant)

    try:
      assert restored.guid.hex == original_guid
      assert _tenant_state(db, restored) == before
      restored_zip = tmp_path / restored.guid.hex / "files" / f"{file_hash}.zip"
      assert restored_zip.exists(), f"Expected restored file at {restored_zip}"
      with zf_mod.ZipFile(restored_zip) as zf:
        assert zf.read(zf.namelist()[0]) == b"fake pdf content"
    finally:
      _delete_tenant_for_backup(tmp_path, restored)
