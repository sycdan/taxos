from unittest.mock import patch
from uuid import UUID
import json
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
  bucket_name: str, vendor: str, total: float, date: str = "2024-06-01T10:00:00"
):
  from taxos.allocation.entity import Allocation
  from taxos.bucket.create.command import CreateBucket
  from taxos.receipt.create.command import CreateReceipt

  bucket = CreateBucket(name=bucket_name).execute()
  allocs = {Allocation(bucket, total)}
  CreateReceipt(
    vendor=vendor, total=total, date=date, timezone="UTC", allocations=allocs
  ).execute()
  return bucket


class TestBackupRestore:
  @pytest.mark.integration
  def test_backup_writes_flat_dir_format(self, tmp_path):
    """Backup writes per-entity state.json files in the flat-directory format."""
    from taxos.tenant.backup.command import BackupTenant

    tenant = _make_tenant_for_backup(tmp_path, "Backup Test")
    _set_context_tenant(tenant)
    bucket = _create_test_data("Travel", "Airline", 500.0)

    with patch("taxos.BACKUPS_DIR", tmp_path / "backups"):
      dest = BackupTenant().execute()

    assert dest.is_dir()

    # Tenant state
    tenant_state = json.loads((dest / "state.json").read_text())
    assert tenant_state["guid"] == str(tenant.guid)
    assert tenant_state["name"] == "Backup Test"

    # Bucket
    bucket_files = list((dest / "buckets").glob("*/state.json"))
    assert len(bucket_files) == 1
    b = json.loads(bucket_files[0].read_text())
    assert b["name"] == "Travel"

    # Vendor
    vendor_files = list((dest / "vendors").glob("*/state.json"))
    assert len(vendor_files) == 1
    v = json.loads(vendor_files[0].read_text())
    assert v["name"] == "Airline"

    # Receipt — vendor field must be a GUID, not a name
    receipt_files = list((dest / "receipts").glob("*/state.json"))
    assert len(receipt_files) == 1
    r = json.loads(receipt_files[0].read_text())
    assert r["total"] == 500.0
    assert r["vendor"] != "Airline", "receipt should store vendor GUID, not name"
    from taxos.tools.guid import parse_guid

    assert parse_guid(r["vendor"]) is not None, "vendor field should be a valid GUID"
    assert len(r["allocations"]) == 1
    assert r["allocations"][0]["amount"] == 500.0
    assert "vendor_ref" in r

    _delete_tenant_for_backup(tmp_path, tenant)

  @pytest.mark.integration
  def test_backup_zip_creates_archive(self, tmp_path):
    """BackupTenant(zip=True) creates a .zip archive instead of a directory."""
    from taxos.tenant.backup.command import BackupTenant

    tenant = _make_tenant_for_backup(tmp_path, "Zip Test")
    _set_context_tenant(tenant)
    _create_test_data("Supplies", "Staples", 99.0)

    with patch("taxos.BACKUPS_DIR", tmp_path / "backups"):
      dest = BackupTenant(zip=True).execute()

    assert dest.suffix == ".zip"
    assert dest.is_file()

    import zipfile

    with zipfile.ZipFile(dest) as zf:
      names = zf.namelist()
    assert any(n == "state.json" for n in names)
    assert any(n.startswith("buckets/") for n in names)
    assert any(n.startswith("vendors/") for n in names)
    assert any(n.startswith("receipts/") for n in names)

    _delete_tenant_for_backup(tmp_path, tenant)

  @pytest.mark.integration
  def test_restore_from_backup_dir_preserves_tenant_guid(self, tmp_path):
    """Round-trip: backup to flat-dir, restore, verify data and GUID are preserved."""
    from taxos import db
    from taxos.tenant.backup.command import BackupTenant
    from taxos.tenant.restore.command import RestoreTenant

    src = _make_tenant_for_backup(tmp_path, "Source Tenant")
    _set_context_tenant(src)
    _create_test_data("Office", "Staples", 45.0, "2024-03-01T09:00:00")

    original_guid = src.guid.hex
    with patch("taxos.BACKUPS_DIR", tmp_path / "backups"):
      backup_dir = BackupTenant().execute()
    _delete_tenant_for_backup(tmp_path, src)

    with patch("taxos.tenant.tools.TENANTS_DIR", tmp_path):
      token = RestoreTenant(source=backup_dir, name="Restored Tenant").execute()

    tenant = token.tenant
    assert isinstance(tenant, Tenant), "Expected tenant in access token"

    try:
      assert tenant.guid.hex == original_guid

      buckets = db.query(
        "MATCH (b:Bucket) RETURN b.name AS name", database=tenant.db_name
      )
      assert len(buckets) == 1
      assert buckets[0]["name"] == "Office"

      rows = db.query(
        """
        MATCH (r:Receipt)-[:FROM_VENDOR]->(v:Vendor)
        OPTIONAL MATCH (r)-[a:ALLOCATED_TO]->(b)
        RETURN v.name AS vendor, collect(a.amount) AS amounts
        """,
        database=tenant.db_name,
      )
      assert rows[0]["vendor"] == "Staples"
      assert rows[0]["amounts"] == [45.0]
    finally:
      _delete_tenant_for_backup(tmp_path, tenant)

  @pytest.mark.integration
  def test_restore_from_backup_zip_preserves_tenant_guid(self, tmp_path):
    """Round-trip: backup to zip, restore from zip, verify data and GUID."""
    from taxos import db
    from taxos.tenant.backup.command import BackupTenant
    from taxos.tenant.restore.command import RestoreTenant

    src = _make_tenant_for_backup(tmp_path, "Zip Source")
    _set_context_tenant(src)
    _create_test_data("Hardware", "Home Depot", 200.0, "2024-07-15T10:00:00")

    original_guid = src.guid.hex
    with patch("taxos.BACKUPS_DIR", tmp_path / "backups"):
      backup_zip = BackupTenant(zip=True).execute()
    _delete_tenant_for_backup(tmp_path, src)

    with patch("taxos.tenant.tools.TENANTS_DIR", tmp_path):
      token = RestoreTenant(source=backup_zip, name="Zip Restored").execute()

    tenant = token.tenant
    assert isinstance(tenant, Tenant)

    try:
      assert tenant.guid.hex == original_guid
      rows = db.query(
        """
        MATCH (r:Receipt)-[:FROM_VENDOR]->(v:Vendor)
        OPTIONAL MATCH (r)-[a:ALLOCATED_TO]->(b)
        RETURN v.name AS vendor, collect(a.amount) AS amounts
        """,
        database=tenant.db_name,
      )
      assert rows[0]["vendor"] == "Home Depot"
      assert rows[0]["amounts"] == [200.0]
    finally:
      _delete_tenant_for_backup(tmp_path, tenant)

  @pytest.mark.integration
  def test_restore_from_flat_dir_legacy_vendor_name(self, tmp_path):
    """Restore from old flat-file directory where receipt vendor field is a name."""
    from taxos import db
    from taxos.tenant.restore.command import RestoreTenant

    tenant_guid = "33333333-3333-3333-3333-333333333333"
    bucket_guid = "11111111-1111-1111-1111-111111111111"
    receipt_guid = "22222222-2222-2222-2222-222222222222"
    vendor_guid = "44444444-4444-4444-4444-444444444444"

    flat_dir = tmp_path / tenant_guid.replace("-", "")

    bucket_dir = flat_dir / "buckets" / bucket_guid.replace("-", "")
    bucket_dir.mkdir(parents=True)
    (bucket_dir / "state.json").write_text(
      json.dumps({"guid": bucket_guid, "name": "Food"})
    )

    vendor_dir = flat_dir / "vendors" / vendor_guid.replace("-", "")
    vendor_dir.mkdir(parents=True)
    (vendor_dir / "state.json").write_text(
      json.dumps({"guid": vendor_guid, "name": "Grocery Store"})
    )

    receipt_dir = flat_dir / "receipts" / receipt_guid.replace("-", "")
    receipt_dir.mkdir(parents=True)
    (receipt_dir / "state.json").write_text(
      json.dumps(
        {
          "guid": receipt_guid,
          "vendor": "Grocery Store",  # legacy: name, not GUID
          "total": 120.0,
          "date": "2024-05-10T14:00:00",
          "timezone": "UTC",
          "allocations": [{"bucket": bucket_guid, "amount": 120.0}],
          "vendor_ref": "INV-LEGACY-001",
          "notes": "weekly shop",
          "hash": "",
        }
      )
    )

    with patch("taxos.tenant.tools.TENANTS_DIR", tmp_path):
      token = RestoreTenant(source=flat_dir, name="Flat Test", nuke=True).execute()

    tenant = token.tenant
    assert isinstance(tenant, Tenant)

    try:
      rows = db.query(
        """
        MATCH (r:Receipt)-[:FROM_VENDOR]->(v:Vendor)
        RETURN v.name AS vendor, r.total AS total, r.notes AS notes, r.reference AS reference
        """,
        database=tenant.db_name,
      )
      assert rows[0]["vendor"] == "Grocery Store"
      assert rows[0]["total"] == 120.0
      assert rows[0]["notes"] == "weekly shop"
      assert rows[0]["reference"] == "INV-LEGACY-001"
    finally:
      _delete_tenant_for_backup(tmp_path, tenant)
