from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest

from taxos.allocation.entity import Allocation
from taxos.bucket.entity import BucketRef
from taxos.receipt.entity import Receipt, ReceiptRef
from taxos.tenant.entity import Tenant

TENANT = Tenant(guid=UUID("01930000-0000-7000-8000-000000000001"), name="Test")
RECEIPT_GUID = UUID("01930000-0000-7000-8000-000000000010")
BUCKET_GUID = UUID("01930000-0000-7000-8000-000000000020")

DATE = datetime(2024, 3, 15, 12, 0, 0)
DATE_ISO = "2024-03-15T12:00:00"


def _ctx(tenant=TENANT):
  from taxos.context.entity import Context

  return Context(tenant=tenant)


def _receipt(**kwargs):
  defaults = dict(
    guid=RECEIPT_GUID,
    vendor="Acme",
    total=100.0,
    date=DATE,
    timezone="UTC",
  )
  defaults.update(kwargs)
  return Receipt(**defaults)


def _node(props: dict):
  """Fake neo4j Node-like object."""
  n = MagicMock()
  n.__getitem__ = lambda self, k: props[k]
  n.get = lambda k, default=None: props.get(k, default)
  return n


# ---------------------------------------------------------------------------
# save
# ---------------------------------------------------------------------------


class TestSaveReceiptHandler:
  @pytest.mark.unit
  def test_merges_receipt_node(self):
    from taxos.receipt.save.handler import handle
    from taxos.receipt.save.command import SaveReceipt
    from taxos.context.tools import set_context

    set_context(_ctx())
    r = _receipt()
    with patch("taxos.receipt.save.handler.db") as mock_db:
      handle(SaveReceipt(receipt=r))

    first_call = mock_db.run.call_args_list[0]
    assert "MERGE" in first_call[0][0]
    assert first_call[0][1]["guid"] == RECEIPT_GUID.hex

  @pytest.mark.unit
  def test_writes_allocation_edges(self):
    from taxos.receipt.save.handler import handle
    from taxos.receipt.save.command import SaveReceipt
    from taxos.context.tools import set_context

    set_context(_ctx())
    r = _receipt(allocations={Allocation(BucketRef(BUCKET_GUID.hex), 50.0)})
    with patch("taxos.receipt.save.handler.db") as mock_db:
      handle(SaveReceipt(receipt=r))

    cypher_calls = [c[0][0] for c in mock_db.run.call_args_list]
    assert any("ALLOCATED_TO" in c and "CREATE" in c for c in cypher_calls)


# ---------------------------------------------------------------------------
# load
# ---------------------------------------------------------------------------


class TestLoadReceiptHandler:
  @pytest.mark.unit
  def test_returns_receipt(self):
    from taxos.receipt.load.handler import handle
    from taxos.receipt.load.query import LoadReceipt
    from taxos.context.tools import set_context

    set_context(_ctx())
    node = _node(
      {
        "guid": RECEIPT_GUID.hex,
        "vendor": "Acme",
        "total": 100.0,
        "date": DATE_ISO,
        "timezone": "UTC",
        "notes": "",
        "hash": "",
        "reference": "",
      }
    )
    record = MagicMock()
    record.__getitem__ = lambda self, k: node if k == "r" else []

    with patch("taxos.receipt.load.handler.db") as mock_db:
      mock_db.query.return_value = [record]
      result = handle(LoadReceipt(ref=ReceiptRef(RECEIPT_GUID.hex)))

    assert result.guid == RECEIPT_GUID
    assert result.vendor == "Acme"

  @pytest.mark.unit
  def test_raises_does_not_exist(self):
    from taxos.receipt.load.handler import handle
    from taxos.receipt.load.query import LoadReceipt
    from taxos.context.tools import set_context

    set_context(_ctx())
    with patch("taxos.receipt.load.handler.db") as mock_db:
      mock_db.query.return_value = []
      with pytest.raises(Receipt.DoesNotExist):
        handle(LoadReceipt(ref=ReceiptRef(RECEIPT_GUID.hex)))


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


class TestDeleteReceiptHandler:
  @pytest.mark.unit
  def test_returns_true_when_deleted(self):
    from taxos.receipt.delete.handler import handle
    from taxos.receipt.delete.command import DeleteReceipt
    from taxos.context.tools import set_context

    set_context(_ctx())
    row = MagicMock()
    row.__getitem__ = lambda self, k: 1

    with patch("taxos.receipt.delete.handler.db") as mock_db:
      mock_db.query.return_value = [row]
      result = handle(DeleteReceipt(ref=RECEIPT_GUID.hex))

    assert result is True
    assert "DETACH DELETE" in mock_db.query.call_args[0][0]

  @pytest.mark.unit
  def test_returns_false_when_not_found(self):
    from taxos.receipt.delete.handler import handle
    from taxos.receipt.delete.command import DeleteReceipt
    from taxos.context.tools import set_context

    set_context(_ctx())
    row = MagicMock()
    row.__getitem__ = lambda self, k: 0

    with patch("taxos.receipt.delete.handler.db") as mock_db:
      mock_db.query.return_value = [row]
      result = handle(DeleteReceipt(ref=RECEIPT_GUID.hex))

    assert result is False


# ---------------------------------------------------------------------------
# integration
# ---------------------------------------------------------------------------


class TestReceiptLifecycleIntegration:
  @pytest.mark.integration
  def test_crud_roundtrip_with_allocation(self, tmp_path):
    from taxos.bucket.create.command import CreateBucket
    from taxos.receipt.create.command import CreateReceipt
    from taxos.receipt.load.query import LoadReceipt
    from taxos.receipt.update.command import UpdateReceipt
    from taxos.receipt.delete.command import DeleteReceipt
    from taxos.tenant.create.command import CreateTenant
    from taxos.tenant.delete.command import DeleteTenant
    from taxos.context.entity import Context
    from taxos.context.tools import set_context

    with patch("taxos.tenant.tools.TENANTS_DIR", tmp_path):
      tenant = CreateTenant(name="Receipt Integration Test").execute()

    set_context(Context(tenant=tenant))
    try:
      bucket = CreateBucket(name="Travel").execute()

      # create with allocation
      alloc = Allocation(BucketRef(bucket.guid.hex), 80.0)
      receipt = CreateReceipt(
        vendor="Acme Hotels",
        total=100.0,
        date="2024-03-15T12:00:00",
        timezone="UTC",
        allocations={alloc},
        notes="Business trip",
      ).execute()

      assert receipt.vendor == "Acme Hotels"
      assert receipt.total == 100.0

      # load — check allocations round-tripped
      loaded = LoadReceipt(ref=ReceiptRef(receipt.guid.hex)).execute()
      assert loaded.guid == receipt.guid
      assert len(loaded.allocations) == 1
      assert next(iter(loaded.allocations)).amount == 80.0

      # update
      updated = UpdateReceipt(
        ref=ReceiptRef(receipt.guid.hex),
        vendor="Acme Hotels",
        total=120.0,
        date="2024-03-15T12:00:00",
        timezone="UTC",
        allocations={Allocation(BucketRef(bucket.guid.hex), 120.0)},
      ).execute()
      assert updated.total == 120.0

      reloaded = LoadReceipt(ref=ReceiptRef(receipt.guid.hex)).execute()
      assert reloaded.total == 120.0
      assert next(iter(reloaded.allocations)).amount == 120.0

      # delete
      assert DeleteReceipt(ref=receipt.guid.hex).execute() is True
      with pytest.raises(Receipt.DoesNotExist):
        LoadReceipt(ref=ReceiptRef(receipt.guid.hex)).execute()

    finally:
      with patch("taxos.tenant.tools.TENANTS_DIR", tmp_path):
        DeleteTenant(tenant=tenant).execute()

  @pytest.mark.integration
  def test_dashboard_buckets_and_unallocated(self, tmp_path):
    from taxos.bucket.create.command import CreateBucket
    from taxos.receipt.create.command import CreateReceipt
    from taxos.tenant.create.command import CreateTenant
    from taxos.tenant.delete.command import DeleteTenant
    from taxos.tenant.dashboard.get.query import GetDashboard
    from taxos.tenant.dashboard.get.handler import handle
    from taxos.context.entity import Context
    from taxos.context.tools import set_context

    with patch("taxos.tenant.tools.TENANTS_DIR", tmp_path):
      tenant = CreateTenant(name="Dashboard Integration Test").execute()

    set_context(Context(tenant=tenant))
    try:
      bucket = CreateBucket(name="Travel").execute()

      # allocated receipt
      CreateReceipt(
        vendor="Acme",
        total=100.0,
        date="2024-03-15T12:00:00",
        timezone="UTC",
        allocations={Allocation(BucketRef(bucket.guid.hex), 100.0)},
      ).execute()

      # unallocated receipt
      CreateReceipt(
        vendor="Unknown",
        total=50.0,
        date="2024-03-20T09:00:00",
        timezone="UTC",
      ).execute()

      dashboard = handle(GetDashboard())

      assert len(dashboard.buckets) == 1
      assert dashboard.buckets[0].name == "Travel"
      assert dashboard.buckets[0].total_amount == 100.0
      assert dashboard.buckets[0].receipt_count == 1

      assert len(dashboard.unallocated) == 1
      assert dashboard.unallocated[0].vendor == "Unknown"

    finally:
      with patch("taxos.tenant.tools.TENANTS_DIR", tmp_path):
        DeleteTenant(tenant=tenant).execute()
