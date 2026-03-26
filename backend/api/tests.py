"""Integration tests for the GraphQL schema — exercises resolvers against real Neo4j."""
from unittest.mock import patch
from uuid import UUID

import pytest

from taxos.allocation.entity import Allocation
from taxos.bucket.entity import BucketRef
from taxos.tenant.entity import Tenant


@pytest.fixture()
def gql_client(tmp_path):
  """Returns a (execute, teardown) tuple.

  execute(query, variables=None) → dict  (the 'data' key)
  Sets up a fresh tenant + Flask test client wired to the GraphQL server.
  """
  from taxos.tenant.create.command import CreateTenant
  from taxos.tenant.delete.command import DeleteTenant
  from taxos.context.entity import Context
  from taxos.context.tools import set_context
  from api.graphql_server import app, schema
  from ariadne.graphql import graphql_sync

  with patch("taxos.tenant.tools.TENANTS_DIR", tmp_path):
    tenant = CreateTenant(name="GQL Integration Test").execute()

  set_context(Context(tenant=tenant))

  def execute(query: str, variables: dict | None = None) -> dict:
    ok, result = graphql_sync(schema, {"query": query, "variables": variables or {}})
    assert "errors" not in result, result.get("errors")
    return result["data"]

  yield execute

  with patch("taxos.tenant.tools.TENANTS_DIR", tmp_path):
    from taxos.tenant.delete.command import DeleteTenant
    DeleteTenant(tenant=tenant).execute()


@pytest.mark.integration
class TestGraphQLBuckets:
  def test_create_and_query_bucket(self, gql_client):
    data = gql_client("""
      mutation { createBucket(name: "Travel") { guid name } }
    """)
    bucket = data["createBucket"]
    assert bucket["name"] == "Travel"
    assert bucket["guid"]

    data = gql_client(f"""
      query {{ bucket(guid: "{bucket['guid']}") {{ guid name }} }}
    """)
    assert data["bucket"]["name"] == "Travel"

  def test_update_bucket(self, gql_client):
    data = gql_client('mutation { createBucket(name: "Old") { guid } }')
    guid = data["createBucket"]["guid"]

    data = gql_client(f'mutation {{ updateBucket(guid: "{guid}", name: "New") {{ name }} }}')
    assert data["updateBucket"]["name"] == "New"

  def test_delete_bucket(self, gql_client):
    data = gql_client('mutation { createBucket(name: "Temp") { guid } }')
    guid = data["createBucket"]["guid"]

    data = gql_client(f'mutation {{ deleteBucket(guid: "{guid}") }}')
    assert data["deleteBucket"] is True

  def test_list_buckets(self, gql_client):
    gql_client('mutation { createBucket(name: "Alpha") { guid } }')
    gql_client('mutation { createBucket(name: "Beta") { guid } }')

    data = gql_client("query { buckets { name } }")
    names = [b["name"] for b in data["buckets"]]
    assert "Alpha" in names
    assert "Beta" in names


@pytest.mark.integration
class TestGraphQLReceipts:
  def test_create_and_load_receipt(self, gql_client):
    data = gql_client("""
      mutation {
        createReceipt(input: {
          vendor: "Acme"
          total: 100.0
          date: "2024-03-15T12:00:00"
          timezone: "UTC"
        }) { guid vendor total date }
      }
    """)
    r = data["createReceipt"]
    assert r["vendor"] == "Acme"
    assert r["total"] == 100.0

    data = gql_client(f'query {{ receipt(guid: "{r["guid"]}") {{ guid vendor total }} }}')
    assert data["receipt"]["vendor"] == "Acme"

  def test_create_receipt_with_allocation(self, gql_client):
    bucket_guid = gql_client('mutation { createBucket(name: "Travel") { guid } }')["createBucket"]["guid"]

    data = gql_client(f"""
      mutation {{
        createReceipt(input: {{
          vendor: "Hotel"
          total: 200.0
          date: "2024-03-15T12:00:00"
          timezone: "UTC"
          allocations: [{{ bucketGuid: "{bucket_guid}", amount: 200.0 }}]
        }}) {{ guid allocations {{ amount bucket {{ name }} }} }}
      }}
    """)
    allocs = data["createReceipt"]["allocations"]
    assert len(allocs) == 1
    assert allocs[0]["amount"] == 200.0
    assert allocs[0]["bucket"]["name"] == "Travel"

  def test_delete_receipt(self, gql_client):
    data = gql_client("""
      mutation {
        createReceipt(input: { vendor: "X", total: 1.0, date: "2024-01-01T00:00:00", timezone: "UTC" }) { guid }
      }
    """)
    guid = data["createReceipt"]["guid"]
    data = gql_client(f'mutation {{ deleteReceipt(guid: "{guid}") }}')
    assert data["deleteReceipt"] is True


@pytest.mark.integration
class TestGraphQLDashboard:
  def test_dashboard_buckets_and_unallocated(self, gql_client):
    bucket_guid = gql_client('mutation { createBucket(name: "Travel") { guid } }')["createBucket"]["guid"]

    gql_client(f"""
      mutation {{
        createReceipt(input: {{
          vendor: "Acme"
          total: 100.0
          date: "2024-03-15T12:00:00"
          timezone: "UTC"
          allocations: [{{ bucketGuid: "{bucket_guid}", amount: 100.0 }}]
        }}) {{ guid }}
      }}
    """)
    gql_client("""
      mutation {
        createReceipt(input: { vendor: "Misc", total: 50.0, date: "2024-03-20T00:00:00", timezone: "UTC" }) { guid }
      }
    """)

    data = gql_client("""
      query {
        dashboard {
          buckets { name totalAmount receiptCount }
          unallocated { vendor }
        }
      }
    """)
    assert data["dashboard"]["buckets"][0]["name"] == "Travel"
    assert data["dashboard"]["buckets"][0]["totalAmount"] == 100.0
    assert len(data["dashboard"]["unallocated"]) == 1
    assert data["dashboard"]["unallocated"][0]["vendor"] == "Misc"


@pytest.mark.integration
class TestGraphQLVendors:
  def test_vendor_list_and_update(self, gql_client):
    gql_client("""
      mutation {
        createReceipt(input: { vendor: "Acme Corp", total: 10.0, date: "2024-01-01T00:00:00", timezone: "UTC" }) { guid }
      }
    """)

    data = gql_client("query { vendors { guid name } }")
    vendor = next(v for v in data["vendors"] if v["name"] == "Acme Corp")

    data = gql_client(f'mutation {{ updateVendor(guid: "{vendor["guid"]}", name: "Acme Ltd") {{ name }} }}')
    assert data["updateVendor"]["name"] == "Acme Ltd"
