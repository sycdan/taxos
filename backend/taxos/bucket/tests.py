from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest

from taxos.bucket.entity import Bucket, BucketRef
from taxos.tenant.entity import Tenant

TENANT = Tenant(guid=UUID("01930000-0000-7000-8000-000000000001"), name="Test")
BUCKET_GUID = UUID("01930000-0000-7000-8000-000000000002")


def _ctx(tenant=TENANT):
  from taxos.context.entity import Context

  return Context(tenant=tenant)


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------


class TestCreateBucketHandler:
  @pytest.mark.unit
  def test_creates_node_in_neo4j(self):
    from taxos.bucket.create.handler import handle
    from taxos.bucket.create.command import CreateBucket
    from taxos.context.tools import set_context

    set_context(_ctx())
    with patch("taxos.bucket.create.handler.db") as mock_db:
      result = handle(CreateBucket(name="Travel"))

    mock_db.run.assert_called_once()
    cypher, params = mock_db.run.call_args[0]
    assert "CREATE" in cypher
    assert ":Bucket" in cypher
    assert params["name"] == "Travel"
    assert mock_db.run.call_args[1]["database"] == TENANT.db_name
    assert result.name == "Travel"


# ---------------------------------------------------------------------------
# load
# ---------------------------------------------------------------------------


class TestLoadBucketHandler:
  @pytest.mark.unit
  def test_returns_bucket_from_record(self):
    from taxos.bucket.load.handler import handle
    from taxos.bucket.load.query import LoadBucket
    from taxos.context.tools import set_context

    set_context(_ctx())
    mock_record = MagicMock()
    mock_record.__getitem__ = lambda self, k: "Travel" if k == "name" else None

    with patch("taxos.bucket.load.handler.db") as mock_db:
      mock_db.query.return_value = [mock_record]
      result = handle(LoadBucket(ref=BucketRef(BUCKET_GUID.hex)))

    assert result.guid == BUCKET_GUID
    assert result.name == "Travel"

  @pytest.mark.unit
  def test_raises_does_not_exist(self):
    from taxos.bucket.load.handler import handle
    from taxos.bucket.load.query import LoadBucket
    from taxos.context.tools import set_context

    set_context(_ctx())
    with patch("taxos.bucket.load.handler.db") as mock_db:
      mock_db.query.return_value = []
      with pytest.raises(Bucket.DoesNotExist):
        handle(LoadBucket(ref=BucketRef(BUCKET_GUID.hex)))


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------


class TestUpdateBucketHandler:
  @pytest.mark.unit
  def test_updates_name_in_neo4j(self):
    from taxos.bucket.update.handler import handle
    from taxos.bucket.update.command import UpdateBucket
    from taxos.context.tools import set_context

    set_context(_ctx())
    mock_record = MagicMock()
    mock_record.__getitem__ = lambda self, k: "Hotels" if k == "name" else None

    with patch("taxos.bucket.update.handler.db") as mock_db:
      mock_db.query.return_value = [mock_record]
      result = handle(UpdateBucket(ref=BucketRef(BUCKET_GUID.hex), name="Hotels"))

    cypher, params = mock_db.query.call_args[0]
    assert "SET" in cypher
    assert params["name"] == "Hotels"
    assert result.name == "Hotels"

  @pytest.mark.unit
  def test_raises_does_not_exist(self):
    from taxos.bucket.update.handler import handle
    from taxos.bucket.update.command import UpdateBucket
    from taxos.context.tools import set_context

    set_context(_ctx())
    with patch("taxos.bucket.update.handler.db") as mock_db:
      mock_db.query.return_value = []
      with pytest.raises(Bucket.DoesNotExist):
        handle(UpdateBucket(ref=BucketRef(BUCKET_GUID.hex), name="Hotels"))


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


class TestDeleteBucketHandler:
  @pytest.mark.unit
  def test_deletes_node_and_returns_true(self):
    from taxos.bucket.delete.handler import handle
    from taxos.bucket.delete.command import DeleteBucket
    from taxos.context.tools import set_context

    set_context(_ctx())
    mock_record = MagicMock()
    mock_record.__getitem__ = lambda self, k: 1 if k == "n" else None

    with patch("taxos.bucket.delete.handler.db") as mock_db:
      mock_db.query.return_value = [mock_record]
      result = handle(DeleteBucket(ref=BUCKET_GUID.hex))

    cypher, params = mock_db.query.call_args[0]
    assert "DETACH DELETE" in cypher
    assert result is True

  @pytest.mark.unit
  def test_returns_false_when_not_found(self):
    from taxos.bucket.delete.handler import handle
    from taxos.bucket.delete.command import DeleteBucket
    from taxos.context.tools import set_context

    set_context(_ctx())
    mock_record = MagicMock()
    mock_record.__getitem__ = lambda self, k: 0 if k == "n" else None

    with patch("taxos.bucket.delete.handler.db") as mock_db:
      mock_db.query.return_value = [mock_record]
      result = handle(DeleteBucket(ref=BUCKET_GUID.hex))

    assert result is False


# ---------------------------------------------------------------------------
# integration
# ---------------------------------------------------------------------------


class TestBucketLifecycleIntegration:
  @pytest.mark.integration
  def test_crud_roundtrip(self, tmp_path):
    from taxos.bucket.create.command import CreateBucket
    from taxos.bucket.load.query import LoadBucket
    from taxos.bucket.update.command import UpdateBucket
    from taxos.bucket.delete.command import DeleteBucket
    from taxos.tenant.create.command import CreateTenant
    from taxos.tenant.delete.command import DeleteTenant
    from taxos.context.entity import Context
    from taxos.context.tools import set_context

    with patch("taxos.tenant.tools.TENANTS_DIR", tmp_path):
      tenant = CreateTenant(name="Bucket Integration Test").execute()

    set_context(Context(tenant=tenant))
    try:
      # create
      bucket = CreateBucket(name="Travel").execute()
      assert bucket.name == "Travel"

      # load
      loaded = LoadBucket(ref=BucketRef(bucket.guid.hex)).execute()
      assert loaded.guid == bucket.guid
      assert loaded.name == "Travel"

      # update
      updated = UpdateBucket(ref=BucketRef(bucket.guid.hex), name="Hotels").execute()
      assert updated.name == "Hotels"

      # verify update persisted
      reloaded = LoadBucket(ref=BucketRef(bucket.guid.hex)).execute()
      assert reloaded.name == "Hotels"

      # delete
      deleted = DeleteBucket(ref=bucket.guid.hex).execute()
      assert deleted is True

      # confirm gone
      with pytest.raises(Bucket.DoesNotExist):
        LoadBucket(ref=BucketRef(bucket.guid.hex)).execute()

    finally:
      with patch("taxos.tenant.tools.TENANTS_DIR", tmp_path):
        assert DeleteTenant(tenant=tenant).execute() is True
