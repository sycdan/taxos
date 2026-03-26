from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest

from taxos.tenant.entity import Tenant
from taxos.vendor.entity import Vendor, VendorRef

TENANT = Tenant(guid=UUID("01930000-0000-7000-8000-000000000001"), name="Test")
VENDOR_GUID = UUID("01930000-0000-7000-8000-000000000002")


def _ctx(tenant=TENANT):
  from taxos.context.entity import Context
  return Context(tenant=tenant)


def _row(guid=VENDOR_GUID, name="Acme"):
  r = MagicMock()
  r.__getitem__ = lambda self, k: guid.hex if k == "guid" else name
  return r


# ---------------------------------------------------------------------------
# find_or_create
# ---------------------------------------------------------------------------

class TestFindOrCreateVendorHandler:
  @pytest.mark.unit
  def test_merges_and_returns_vendor(self):
    from taxos.vendor.find_or_create.handler import handle
    from taxos.vendor.find_or_create.command import FindOrCreateVendor
    from taxos.context.tools import set_context

    set_context(_ctx())
    with patch("taxos.vendor.find_or_create.handler.db") as mock_db:
      mock_db.query.return_value = [_row(name="Acme")]
      result = handle(FindOrCreateVendor(name="Acme"))

    cypher = mock_db.query.call_args[0][0]
    assert "MERGE" in cypher
    assert result.name == "Acme"

  @pytest.mark.unit
  def test_merge_is_case_insensitive(self):
    from taxos.vendor.find_or_create.handler import handle
    from taxos.vendor.find_or_create.command import FindOrCreateVendor
    from taxos.context.tools import set_context

    set_context(_ctx())
    with patch("taxos.vendor.find_or_create.handler.db") as mock_db:
      mock_db.query.return_value = [_row(name="Acme")]
      handle(FindOrCreateVendor(name="ACME"))

    params = mock_db.query.call_args[0][1]
    assert "name_lower" in mock_db.query.call_args[0][0]
    assert params["name"] == "ACME"


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------

class TestListVendorsHandler:
  @pytest.mark.unit
  def test_returns_sorted_vendors(self):
    from taxos.vendor.list.handler import handle
    from taxos.vendor.list.query import ListVendors
    from taxos.context.tools import set_context

    set_context(_ctx())
    g1 = UUID("01930000-0000-7000-8000-000000000010")
    g2 = UUID("01930000-0000-7000-8000-000000000011")
    r1, r2 = MagicMock(), MagicMock()
    r1.__getitem__ = lambda self, k: g1.hex if k == "guid" else "Zebra"
    r2.__getitem__ = lambda self, k: g2.hex if k == "guid" else "Acme"

    with patch("taxos.vendor.list.handler.db") as mock_db:
      # Cypher returns ORDER BY toLower(name) so we return already sorted
      mock_db.query.return_value = [r2, r1]
      result = handle(ListVendors())

    assert [v.name for v in result] == ["Acme", "Zebra"]

  @pytest.mark.unit
  def test_returns_empty_list(self):
    from taxos.vendor.list.handler import handle
    from taxos.vendor.list.query import ListVendors
    from taxos.context.tools import set_context

    set_context(_ctx())
    with patch("taxos.vendor.list.handler.db") as mock_db:
      mock_db.query.return_value = []
      result = handle(ListVendors())

    assert result == []


# ---------------------------------------------------------------------------
# load
# ---------------------------------------------------------------------------

class TestLoadVendorHandler:
  @pytest.mark.unit
  def test_returns_vendor(self):
    from taxos.vendor.load.handler import handle
    from taxos.vendor.load.query import LoadVendor
    from taxos.context.tools import set_context

    set_context(_ctx())
    mock_record = MagicMock()
    mock_record.__getitem__ = lambda self, k: "Acme"

    with patch("taxos.vendor.load.handler.db") as mock_db:
      mock_db.query.return_value = [mock_record]
      result = handle(LoadVendor(ref=VendorRef(VENDOR_GUID.hex)))

    assert result.guid == VENDOR_GUID
    assert result.name == "Acme"

  @pytest.mark.unit
  def test_raises_does_not_exist(self):
    from taxos.vendor.load.handler import handle
    from taxos.vendor.load.query import LoadVendor
    from taxos.context.tools import set_context

    set_context(_ctx())
    with patch("taxos.vendor.load.handler.db") as mock_db:
      mock_db.query.return_value = []
      with pytest.raises(Vendor.DoesNotExist):
        handle(LoadVendor(ref=VendorRef(VENDOR_GUID.hex)))


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------

class TestUpdateVendorHandler:
  @pytest.mark.unit
  def test_updates_name(self):
    from taxos.vendor.update.handler import handle
    from taxos.vendor.update.command import UpdateVendor
    from taxos.context.tools import set_context

    set_context(_ctx())
    mock_record = MagicMock()
    mock_record.__getitem__ = lambda self, k: "Renamed"

    with patch("taxos.vendor.update.handler.db") as mock_db:
      mock_db.query.return_value = [mock_record]
      result = handle(UpdateVendor(ref=VendorRef(VENDOR_GUID.hex), name="Renamed"))

    cypher = mock_db.query.call_args[0][0]
    assert "SET" in cypher
    assert "name_lower" in cypher
    assert result.name == "Renamed"

  @pytest.mark.unit
  def test_raises_does_not_exist(self):
    from taxos.vendor.update.handler import handle
    from taxos.vendor.update.command import UpdateVendor
    from taxos.context.tools import set_context

    set_context(_ctx())
    with patch("taxos.vendor.update.handler.db") as mock_db:
      mock_db.query.return_value = []
      with pytest.raises(Vendor.DoesNotExist):
        handle(UpdateVendor(ref=VendorRef(VENDOR_GUID.hex), name="Renamed"))


# ---------------------------------------------------------------------------
# integration
# ---------------------------------------------------------------------------

class TestVendorLifecycleIntegration:
  @pytest.mark.integration
  def test_find_or_create_load_update_list(self, tmp_path):
    from taxos.vendor.find_or_create.command import FindOrCreateVendor
    from taxos.vendor.load.query import LoadVendor
    from taxos.vendor.list.query import ListVendors
    from taxos.vendor.update.command import UpdateVendor
    from taxos.tenant.create.command import CreateTenant
    from taxos.tenant.delete.command import DeleteTenant
    from taxos.context.entity import Context
    from taxos.context.tools import set_context

    with patch("taxos.tenant.tools.TENANTS_DIR", tmp_path):
      tenant = CreateTenant(name="Vendor Integration Test").execute()

    set_context(Context(tenant=tenant))
    try:
      # find_or_create — creates
      v1 = FindOrCreateVendor(name="Acme").execute()
      assert v1.name == "Acme"

      # find_or_create — idempotent (case-insensitive)
      v2 = FindOrCreateVendor(name="ACME").execute()
      assert v2.guid == v1.guid

      # load
      loaded = LoadVendor(ref=VendorRef(v1.guid.hex)).execute()
      assert loaded.name == "Acme"

      # update
      updated = UpdateVendor(ref=VendorRef(v1.guid.hex), name="Acme Corp").execute()
      assert updated.name == "Acme Corp"

      # list
      FindOrCreateVendor(name="Zebra").execute()
      vendors = ListVendors().execute()
      names = [v.name for v in vendors]
      assert "Acme Corp" in names
      assert "Zebra" in names
      assert names == sorted(names, key=str.lower)

    finally:
      with patch("taxos.tenant.tools.TENANTS_DIR", tmp_path):
        DeleteTenant(tenant=tenant).execute()
