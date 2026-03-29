"""Integration tests for the GraphQL schema — exercises resolvers against real Neo4j."""

from unittest.mock import patch

import pytest


@pytest.fixture()
def gql(tmp_path):
  """Yields an execute(query, variables) helper bound to a fresh tenant.

  After each test the tenant and its Neo4j database are torn down.
  Asserts no GraphQL errors so tests fail loudly on resolver exceptions.
  """
  from taxos.tenant.create.command import CreateTenant
  from taxos.tenant.delete.command import DeleteTenant
  from taxos.context.entity import Context
  from taxos.context.tools import set_context
  from api.graphql_server import schema
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
    DeleteTenant(tenant=tenant).execute()


# ---------------------------------------------------------------------------
# Buckets
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestBuckets:
  def test_create_persists(self, gql):
    guid = gql('mutation { createBucket(name: "Travel") { guid } }')["createBucket"][
      "guid"
    ]

    fetched = gql(f'query {{ bucket(guid: "{guid}") {{ guid name }} }}')["bucket"]
    assert fetched["name"] == "Travel"
    assert fetched["guid"] == guid

  def test_update_persists(self, gql):
    guid = gql('mutation { createBucket(name: "Old") { guid } }')["createBucket"][
      "guid"
    ]

    gql(f'mutation {{ updateBucket(guid: "{guid}", name: "New") {{ name }} }}')

    fetched = gql(f'query {{ bucket(guid: "{guid}") {{ name }} }}')["bucket"]
    assert fetched["name"] == "New"

  def test_delete_removes_from_db(self, gql):
    guid = gql('mutation { createBucket(name: "Temp") { guid } }')["createBucket"][
      "guid"
    ]

    result = gql(f'mutation {{ deleteBucket(guid: "{guid}") }}')
    assert result["deleteBucket"] is True

    fetched = gql(f'query {{ bucket(guid: "{guid}") {{ guid }} }}')["bucket"]
    assert fetched is None

  def test_list_returns_all(self, gql):
    gql('mutation { createBucket(name: "Alpha") { guid } }')
    gql('mutation { createBucket(name: "Beta") { guid } }')

    names = [b["name"] for b in gql("query { buckets { name } }")["buckets"]]
    assert "Alpha" in names
    assert "Beta" in names

  def test_bucket_total_amount_and_receipt_count(self, gql):
    bucket_guid = gql('mutation { createBucket(name: "Expenses") { guid } }')[
      "createBucket"
    ]["guid"]

    gql(f"""
      mutation {{
        createReceipt(input: {{
          vendor: "Acme"
          total: 80.0
          date: "2024-03-01T00:00:00"
          timezone: "UTC"
          allocations: [{{ bucketGuid: "{bucket_guid}", amount: 80.0 }}]
        }}) {{ guid }}
      }}
    """)

    bucket = gql(f"""
      query {{ bucket(guid: "{bucket_guid}") {{ totalAmount receiptCount }} }}
    """)["bucket"]
    assert bucket["totalAmount"] == 80.0
    assert bucket["receiptCount"] == 1

  def test_bucket_receipts_field(self, gql):
    bucket_guid = gql('mutation { createBucket(name: "Office") { guid } }')[
      "createBucket"
    ]["guid"]

    gql(f"""
      mutation {{
        createReceipt(input: {{
          vendor: "Staples"
          total: 30.0
          date: "2024-03-01T00:00:00"
          timezone: "UTC"
          allocations: [{{ bucketGuid: "{bucket_guid}", amount: 30.0 }}]
        }}) {{ guid }}
      }}
    """)

    receipts = gql(f"""
      query {{ bucket(guid: "{bucket_guid}") {{ receipts {{ vendor total }} }} }}
    """)["bucket"]["receipts"]
    assert len(receipts) == 1
    assert receipts[0]["vendor"] == "Staples"
    assert receipts[0]["total"] == 30.0


# ---------------------------------------------------------------------------
# Receipts
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestReceipts:
  def test_create_persists(self, gql):
    guid = gql("""
      mutation {
        createReceipt(input: {
          vendor: "Acme"
          total: 100.0
          date: "2024-03-15T12:00:00"
          timezone: "UTC"
          notes: "business lunch"
        }) { guid }
      }
    """)["createReceipt"]["guid"]

    fetched = gql(f'query {{ receipt(guid: "{guid}") {{ vendor total notes }} }}')[
      "receipt"
    ]
    assert fetched["vendor"] == "Acme"
    assert fetched["total"] == 100.0
    assert fetched["notes"] == "business lunch"

  def test_create_with_allocation_persists(self, gql):
    bucket_guid = gql('mutation { createBucket(name: "Travel") { guid } }')[
      "createBucket"
    ]["guid"]

    guid = gql(f"""
      mutation {{
        createReceipt(input: {{
          vendor: "Hotel"
          total: 200.0
          date: "2024-03-15T12:00:00"
          timezone: "UTC"
          allocations: [{{ bucketGuid: "{bucket_guid}", amount: 200.0 }}]
        }}) {{ guid }}
      }}
    """)["createReceipt"]["guid"]

    fetched = gql(f"""
      query {{ receipt(guid: "{guid}") {{ allocations {{ amount bucket {{ name }} }} }} }}
    """)["receipt"]
    assert len(fetched["allocations"]) == 1
    assert fetched["allocations"][0]["amount"] == 200.0
    assert fetched["allocations"][0]["bucket"]["name"] == "Travel"

  def test_update_persists(self, gql):
    guid = gql("""
      mutation {
        createReceipt(input: {
          vendor: "Old Vendor"
          total: 50.0
          date: "2024-03-01T00:00:00"
          timezone: "UTC"
        }) { guid }
      }
    """)["createReceipt"]["guid"]

    gql(f"""
      mutation {{
        updateReceipt(guid: "{guid}", input: {{
          vendor: "New Vendor"
          total: 75.0
          date: "2024-03-01T00:00:00"
          timezone: "UTC"
          notes: "updated"
        }}) {{ guid }}
      }}
    """)

    fetched = gql(f'query {{ receipt(guid: "{guid}") {{ vendor total notes }} }}')[
      "receipt"
    ]
    assert fetched["vendor"] == "New Vendor"
    assert fetched["total"] == 75.0
    assert fetched["notes"] == "updated"

  def test_update_replaces_allocations(self, gql):
    b1 = gql('mutation { createBucket(name: "A") { guid } }')["createBucket"]["guid"]
    b2 = gql('mutation { createBucket(name: "B") { guid } }')["createBucket"]["guid"]

    guid = gql(f"""
      mutation {{
        createReceipt(input: {{
          vendor: "X"
          total: 100.0
          date: "2024-03-01T00:00:00"
          timezone: "UTC"
          allocations: [{{ bucketGuid: "{b1}", amount: 100.0 }}]
        }}) {{ guid }}
      }}
    """)["createReceipt"]["guid"]

    gql(f"""
      mutation {{
        updateReceipt(guid: "{guid}", input: {{
          vendor: "X"
          total: 100.0
          date: "2024-03-01T00:00:00"
          timezone: "UTC"
          allocations: [{{ bucketGuid: "{b2}", amount: 100.0 }}]
        }}) {{ guid }}
      }}
    """)

    allocs = gql(
      f'query {{ receipt(guid: "{guid}") {{ allocations {{ bucket {{ name }} }} }} }}'
    )["receipt"]["allocations"]
    assert len(allocs) == 1
    assert allocs[0]["bucket"]["name"] == "B"

  def test_delete_removes_from_db(self, gql):
    guid = gql("""
      mutation {
        createReceipt(input: { vendor: "X", total: 1.0, date: "2024-01-01T00:00:00", timezone: "UTC" }) { guid }
      }
    """)["createReceipt"]["guid"]

    result = gql(f'mutation {{ deleteReceipt(guid: "{guid}") }}')
    assert result["deleteReceipt"] is True

    fetched = gql(f'query {{ receipt(guid: "{guid}") {{ guid }} }}')["receipt"]
    assert fetched is None

  def test_receipts_query_filtered_by_bucket(self, gql):
    b1 = gql('mutation { createBucket(name: "Food") { guid } }')["createBucket"]["guid"]
    b2 = gql('mutation { createBucket(name: "Travel") { guid } }')["createBucket"][
      "guid"
    ]

    gql(f"""
      mutation {{
        createReceipt(input: {{
          vendor: "Restaurant"
          total: 30.0
          date: "2024-01-01T00:00:00"
          timezone: "UTC"
          allocations: [{{ bucketGuid: "{b1}", amount: 30.0 }}]
        }}) {{ guid }}
      }}
    """)
    gql(f"""
      mutation {{
        createReceipt(input: {{
          vendor: "Airline"
          total: 500.0
          date: "2024-01-02T00:00:00"
          timezone: "UTC"
          allocations: [{{ bucketGuid: "{b2}", amount: 500.0 }}]
        }}) {{ guid }}
      }}
    """)

    receipts = gql(f'query {{ receipts(bucket: "{b1}") {{ vendor }} }}')["receipts"]
    assert len(receipts) == 1
    assert receipts[0]["vendor"] == "Restaurant"

  def test_receipts_query_filtered_by_months(self, gql):
    gql("""
      mutation {
        createReceipt(input: { vendor: "Jan", total: 1.0, date: "2024-01-15T00:00:00", timezone: "UTC" }) { guid }
      }
    """)
    gql("""
      mutation {
        createReceipt(input: { vendor: "Feb", total: 1.0, date: "2024-02-15T00:00:00", timezone: "UTC" }) { guid }
      }
    """)

    receipts = gql('query { receipts(months: ["2024-01"]) { vendor } }')["receipts"]
    vendors = [r["vendor"] for r in receipts]
    assert "Jan" in vendors
    assert "Feb" not in vendors


# ---------------------------------------------------------------------------
# Vendors
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestVendors:
  def test_create_via_receipt_and_list(self, gql):
    gql("""
      mutation {
        createReceipt(input: { vendor: "Acme Corp", total: 10.0, date: "2024-01-01T00:00:00", timezone: "UTC" }) { guid }
      }
    """)

    vendors = gql("query { vendors { guid name } }")["vendors"]
    assert any(v["name"] == "Acme Corp" for v in vendors)

  def test_update_persists(self, gql):
    gql("""
      mutation {
        createReceipt(input: { vendor: "Old Name", total: 10.0, date: "2024-01-01T00:00:00", timezone: "UTC" }) { guid }
      }
    """)
    vendors = gql("query { vendors { guid name } }")["vendors"]
    guid = next(v["guid"] for v in vendors if v["name"] == "Old Name")

    gql(f'mutation {{ updateVendor(guid: "{guid}", name: "New Name") {{ name }} }}')

    vendors = gql("query { vendors { guid name } }")["vendors"]
    names = [v["name"] for v in vendors]
    assert "New Name" in names
    assert "Old Name" not in names

  def test_vendor_receipts_field(self, gql):
    gql("""
      mutation {
        createReceipt(input: { vendor: "Staples", total: 25.0, date: "2024-01-01T00:00:00", timezone: "UTC" }) { guid }
      }
    """)
    gql("""
      mutation {
        createReceipt(input: { vendor: "Staples", total: 40.0, date: "2024-02-01T00:00:00", timezone: "UTC" }) { guid }
      }
    """)

    vendors = gql("query { vendors { guid name } }")["vendors"]
    guid = next(v["guid"] for v in vendors if v["name"] == "Staples")

    receipts = gql(f'query {{ vendor(guid: "{guid}") {{ receipts {{ total }} }} }}')[
      "vendor"
    ]["receipts"]
    totals = sorted(r["total"] for r in receipts)
    assert totals == [25.0, 40.0]

