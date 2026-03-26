from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest

from taxos.tenant.entity import Tenant, TenantRef


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
      patch.object(type(tenant), "content_dir", new_callable=lambda: property(lambda self: tmp_path / self.guid.hex)),
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
      patch.object(type(tenant), "content_dir", new_callable=lambda: property(lambda self: tmp_path / "nonexistent")),
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
