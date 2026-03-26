# Migration: Neo4j + GraphQL

Replace flat-file JSON persistence and Connect-RPC with a Neo4j graph database and
a GraphQL API (Ariadne + Apollo Client).

## Decisions

| Question | Decision | Reason |
|---|---|---|
| Tenant isolation | One Neo4j database per tenant (`CREATE DATABASE`) | Mirrors current directory-per-tenant; instant create/drop; clean test isolation |
| File attachments | Stay on filesystem (`data/tenants/<guid>/files/`) | Already content-addressed by SHA-256; no reason to move |
| Auth tokens | Stay on filesystem (`data/access_tokens/`) | Cross-tenant; checked before any DB access; no change needed |
| GraphQL library | Ariadne (schema-first) | Domain entities returned from resolvers directly — no parallel GQL type classes; SDL is the shared contract |
| Backend language | Keep Python | Scaf CLI, debugpy, CQRS handler pattern all preserved; worth more than `@neo4j/graphql` auto-gen |
| Protobuf | Remove | GraphQL SDL + Ariadne replaces it as the API contract |
| Frontend client | Apollo Client + graphql-codegen | Replaces Connect-RPC; typed hooks generated from SDL |

## Graph model

Each tenant gets its own Neo4j database named `t{tenant_guid_hex}` (hex prefix avoids
leading-digit issue). No cross-tenant nodes; tenant isolation is structural, not just
a `WHERE tenantId =` filter.

Within each tenant database:
```
(:Receipt {guid, total, date, timezone, vendor, reference, notes, hash})
(:Vendor  {guid, name, name_lower})
(:Bucket  {guid, name})
(:Receipt)-[:FROM_VENDOR]->(:Vendor)
(:Receipt)-[:ALLOCATED_TO {amount}]->(:Bucket)
```

`reference` is the vendor-provided identifier printed on the document (invoice number,
order number, etc.). Renamed from `reference` — that name implied a foreign key.
`Bucket.created_at` / `updated_at` exist in the proto but are absent from the domain
entity and never populated; they are dropped here.

## Filesystem layer (unchanged)

Three things stay on the filesystem — all identity/auth metadata, none of it business data:

```
data/
├── access_tokens/{hash}.json        # token hash → tenant GUID
└── tenants/{guid}/
    ├── state.json                   # tenant name + token_count (unchanged)
    └── files/{sha256}.zip           # receipt attachments (unchanged)
```

`LoadTenant` continues to read `state.json` as today. `Tenant.content_dir` is kept
(it now only matters for the `files/` subdirectory). `token_count` stays in `state.json`
since it drives deterministic token hash generation and is auth metadata, not business data.

## New dependencies

**Backend** (`backend/requirements.txt`):
```
neo4j>=5.0           # official Python driver
ariadne>=0.23        # schema-first GraphQL
```

Remove: `grpcio`, `grpcio-tools`, `protobuf`

**Frontend** (`frontend/package.json`):
```
@apollo/client
graphql
graphql-tag
```
Dev:
```
@graphql-codegen/cli
@graphql-codegen/typescript
@graphql-codegen/typescript-operations
@graphql-codegen/typescript-react-apollo
```

Remove: `@connectrpc/connect`, `@connectrpc/connect-web`, `@bufbuild/protobuf`

## Migration phases

---

### Phase 0 — Infrastructure ✅

**docker-compose.yml**: add Neo4j service
```yaml
neo4j:
  image: neo4j:5
  environment:
    NEO4J_AUTH: neo4j/password
    NEO4J_PLUGINS: '["apoc"]'    # for future export/import
  ports:
    - "7474:7474"   # browser
    - "7687:7687"   # bolt
  volumes:
    - neo4j_data:/data
```

**`backend/taxos/db.py`** (new file):
```python
import os
from neo4j import GraphDatabase

_driver = None

def get_driver():
    global _driver
    if _driver is None:
        uri  = os.environ.get("NEO4J_URI", "bolt://neo4j:7687")
        auth = (os.environ.get("NEO4J_USER", "neo4j"),
                os.environ.get("NEO4J_PASSWORD", "password"))
        _driver = GraphDatabase.driver(uri, auth=auth)
    return _driver

def query(cypher: str, params: dict = None, *, database: str) -> list:
    return get_driver().execute_query(cypher, params or {}, database_=database).records

def run(cypher: str, params: dict = None, *, database: str) -> None:
    get_driver().execute_query(cypher, params or {}, database_=database)
```

`database` is always keyword-only to prevent accidental omission.

---

### Phase 1 — Tenant entity + lifecycle handlers ✅

**`backend/taxos/tenant/entity.py`**: add `db_name` property, remove `content_dir` and
`state_file` cached properties (they reference the filesystem hierarchy that disappears).

```python
@property
def db_name(self) -> str:
    """Neo4j database name. t-prefix ensures it never starts with a digit."""
    return f"t{self.guid.hex}"
```

**`backend/taxos/tenant/create/handler.py`**: write `state.json` as today, then
create the Neo4j database:
```python
from taxos import db

def handle(command: CreateTenant) -> Tenant:
    tenant = Tenant(guid.uuid7(), command.name)
    # state.json (name + token_count) stays on filesystem — unchanged
    state_file = get_state_file(tenant.guid)
    os.makedirs(state_file.parent, exist_ok=True)
    json.dump(tenant, state_file)
    # Create the isolated graph database for this tenant's business data
    db.run(f"CREATE DATABASE {tenant.db_name} IF NOT EXISTS", database="system")
    return tenant
```

Note: `CREATE DATABASE` is a DDL command — Neo4j does not support parameterised DB
names, so the name is interpolated. `db_name` is derived from a UUID hex (alphanumeric
only), so this is safe.

**`backend/taxos/tenant/delete/handler.py`**: delete `state.json` directory as today,
then drop the Neo4j database:
```python
def handle(command: DeleteTenant) -> None:
    tenant = require_tenant(command.ref)
    # Remove identity metadata + uploaded files from filesystem (unchanged)
    content_dir = tenant.content_dir
    if content_dir.exists():
        shutil.rmtree(content_dir)
    # Drop the tenant's graph database (equivalent to the old rm -rf for business data)
    db.run(f"DROP DATABASE {tenant.db_name} IF EXISTS DESTROY DATA", database="system")
```

**`backend/taxos/tenant/load/handler.py`**: unchanged — still reads `state.json`.

**Delete**: `backend/taxos/tenant/tools.py` (get_content_dir, get_state_file, get_files_dir
for tenant — file path helpers no longer needed for tenant itself; files_dir stays for
attachment storage).

---

### Phase 2 — Bucket handlers ✅

All four handlers replace file I/O with Cypher. No relationships to manage.

**`bucket/create/handler.py`**:
```python
def handle(command: CreateBucket) -> Bucket:
    tenant = require_tenant()
    bucket = Bucket(guid.uuid7(), command.name)
    db.run(
        "CREATE (:Bucket {guid: $guid, name: $name})",
        {"guid": bucket.guid.hex, "name": bucket.name},
        database=tenant.db_name,
    )
    return bucket
```

**`bucket/load/handler.py`**:
```python
def handle(query: LoadBucket) -> Bucket:
    tenant = require_tenant()
    records = db.query(
        "MATCH (b:Bucket {guid: $guid}) RETURN b.name AS name",
        {"guid": query.ref.guid.hex},
        database=tenant.db_name,
    )
    if not records:
        raise Bucket.DoesNotExist(query.ref.guid)
    return Bucket(query.ref.guid, records[0]["name"])
```

**`bucket/update/handler.py`**:
```python
def handle(command: UpdateBucket) -> Bucket:
    tenant = require_tenant()
    records = db.query(
        "MATCH (b:Bucket {guid: $guid}) SET b.name = $name RETURN b.name AS name",
        {"guid": command.ref.guid.hex, "name": command.name},
        database=tenant.db_name,
    )
    if not records:
        raise Bucket.DoesNotExist(command.ref.guid)
    return Bucket(command.ref.guid, records[0]["name"])
```

**`bucket/delete/handler.py`**:
```python
def handle(command: DeleteBucket) -> bool:
    tenant = require_tenant()
    # Detach also removes ALLOCATED_TO edges from receipts
    result = db.query(
        "MATCH (b:Bucket {guid: $guid}) DETACH DELETE b RETURN count(b) AS n",
        {"guid": command.ref.guid.hex},
        database=tenant.db_name,
    )
    return result[0]["n"] > 0
```

**Delete entire `bucket/repo/` subtree** — `BucketRepo`, `LoadBucketRepo`, `bucket/repo/load/`
are no longer needed.

---

### Phase 3 — Vendor handlers

**`vendor/find_or_create/handler.py`**:
```python
def handle(command: FindOrCreateVendor) -> Vendor:
    tenant = require_tenant()
    records = db.query(
        """
        MERGE (v:Vendor {name_lower: toLower($name)})
        ON CREATE SET v.guid = $new_guid, v.name = $name
        RETURN v.guid AS guid, v.name AS name
        """,
        {"name": command.name, "new_guid": guid_tools.uuid7().hex},
        database=tenant.db_name,
    )
    row = records[0]
    return Vendor(row["guid"], row["name"])
```

`MERGE` is atomic — find-or-create with no race condition. `new_guid` is only consumed
if the node is actually created.

**`vendor/list/handler.py`**:
```python
def handle(query: ListVendors) -> list[Vendor]:
    tenant = require_tenant()
    records = db.query(
        "MATCH (v:Vendor) RETURN v.guid AS guid, v.name AS name ORDER BY toLower(v.name)",
        database=tenant.db_name,
    )
    return [Vendor(r["guid"], r["name"]) for r in records]
```

**`vendor/load/handler.py`**:
```python
def handle(query: LoadVendor) -> Vendor:
    tenant = require_tenant()
    records = db.query(
        "MATCH (v:Vendor {guid: $guid}) RETURN v.name AS name",
        {"guid": query.ref.guid.hex},
        database=tenant.db_name,
    )
    if not records:
        raise Vendor.DoesNotExist(query.ref.guid)
    return Vendor(query.ref.guid, records[0]["name"])
```

**`vendor/update/handler.py`**:
```python
def handle(command: UpdateVendor) -> Vendor:
    tenant = require_tenant()
    records = db.query(
        """
        MATCH (v:Vendor {guid: $guid})
        SET v.name = $name, v.name_lower = toLower($name)
        RETURN v.name AS name
        """,
        {"guid": command.ref.guid.hex, "name": command.name},
        database=tenant.db_name,
    )
    if not records:
        raise Vendor.DoesNotExist(command.ref.guid)
    return Vendor(command.ref.guid, records[0]["name"])
```

**Delete entire `vendor/repo/` subtree** — `VendorRepo`, `LoadVendorRepo` gone.

---

### Phase 4 — Receipt handlers

`receipt/save/handler.py` is the central write path (used by both create and update).
It replaces JSON file write with three Cypher operations: upsert node, link vendor,
upsert allocation edges.

```python
def handle(command: SaveReceipt):
    tenant = require_tenant()
    r = command.receipt

    db.run(
        """
        MERGE (r:Receipt {guid: $guid})
        SET r.total = $total, r.date = $date, r.timezone = $timezone,
            r.vendor = $vendor, r.notes = $notes, r.hash = $hash,
            r.reference = $reference
        """,
        {"guid": r.guid.hex, "total": r.total, "date": r.date.isoformat(),
         "timezone": r.timezone, "vendor": r.vendor or "",
         "notes": r.notes or "", "hash": r.hash or "",
         "reference": r.reference or ""},
        database=tenant.db_name,
    )

    if r.vendor:
        db.run(
            """
            MATCH (r:Receipt {guid: $receipt_guid})
            MATCH (v:Vendor {name_lower: toLower($vendor_name)})
            MERGE (r)-[:FROM_VENDOR]->(v)
            """,
            {"receipt_guid": r.guid.hex, "vendor_name": r.vendor},
            database=tenant.db_name,
        )

    # Remove stale allocation edges before re-writing (handles updates)
    db.run(
        "MATCH (r:Receipt {guid: $guid})-[a:ALLOCATED_TO]->() DELETE a",
        {"guid": r.guid.hex},
        database=tenant.db_name,
    )
    for alloc in r.allocations:
        db.run(
            """
            MATCH (r:Receipt {guid: $receipt_guid})
            MATCH (b:Bucket  {guid: $bucket_guid})
            CREATE (r)-[:ALLOCATED_TO {amount: $amount}]->(b)
            """,
            {"receipt_guid": r.guid.hex,
             "bucket_guid": alloc.bucket.guid.hex,
             "amount": alloc.amount},
            database=tenant.db_name,
        )
    return r
```

**`receipt/load/handler.py`**: MATCH receipt + related nodes in one query.

```python
def handle(query: LoadReceipt) -> Receipt:
    tenant = require_tenant()
    records = db.query(
        """
        MATCH (r:Receipt {guid: $guid})
        OPTIONAL MATCH (r)-[a:ALLOCATED_TO]->(b:Bucket)
        RETURN r, collect({bucket: b.guid, amount: a.amount}) AS allocations
        """,
        {"guid": query.ref.guid.hex},
        database=tenant.db_name,
    )
    if not records:
        raise Receipt.DoesNotExist(query.ref.guid)
    return _record_to_receipt(records[0])
```

**`receipt/delete/handler.py`**: DETACH DELETE removes all edges.
```python
def handle(command: DeleteReceipt) -> bool:
    tenant = require_tenant()
    result = db.query(
        "MATCH (r:Receipt {guid: $guid}) DETACH DELETE r RETURN count(r) AS n",
        {"guid": command.ref.guid.hex},
        database=tenant.db_name,
    )
    return result[0]["n"] > 0
```

**Delete entire `receipt/repo/` subtree** — `ReceiptRepo`, `LoadReceiptRepo`,
`SaveReceiptRepo`, `UpdateReceiptRepo` all gone.  This also removes `receipt/tools.py`
(get_state_file) and the `receipt/attach_file/handler.py` reference to `UpdateReceiptRepo`.

The `attach_file` and `download_file` handlers change only in that the file path now
comes from `tenant.files_dir` (computed from `DATA_DIR` + tenant guid) rather than
from `tenant.content_dir`.

---

### Phase 5 — Dashboard query

Replace the file-walking aggregation with a single Cypher query:

```cypher
MATCH (b:Bucket)
OPTIONAL MATCH (b)<-[a:ALLOCATED_TO]-(r:Receipt)
WITH b, sum(a.amount) AS total, count(r) AS receipt_count
RETURN b.guid AS guid, b.name AS name, total, receipt_count
ORDER BY b.name
```

Unallocated receipts:
```cypher
MATCH (r:Receipt)
WHERE NOT (r)-[:ALLOCATED_TO]->()
RETURN r
```

Both queries replace the current multi-pass repo walk in `tenant/dashboard/get/handler.py`.

---

### Phase 6 — Ariadne GraphQL layer (new `backend/api/graphql_server.py`)

The SDL lives in `backend/api/schema.graphql`. Flask mounts it at `/graphql`.
The `require_auth` decorator from the existing server is reused unchanged.

**`backend/api/schema.graphql`**:
```graphql
type Query {
  vendors: [Vendor!]!
  vendor(guid: ID!): Vendor
  buckets: [Bucket!]!
  bucket(guid: ID!): Bucket
  receipts(vendorGuid: ID, bucketGuid: ID, months: [String!]): [Receipt!]!
  receipt(guid: ID!): Receipt
  dashboard(months: [String!]): Dashboard
}

type Mutation {
  createBucket(name: String!): Bucket!
  updateBucket(guid: ID!, name: String!): Bucket!
  deleteBucket(guid: ID!): Boolean!

  createReceipt(input: ReceiptInput!): Receipt!
  updateReceipt(guid: ID!, input: ReceiptInput!): Receipt!
  deleteReceipt(guid: ID!): Boolean!

  updateVendor(guid: ID!, name: String!): Vendor!

  uploadReceiptFile(hash: String!, filename: String!, data: String!): FileInfo!
}

type Vendor {
  guid: ID!
  name: String!
  receipts: [Receipt!]!
}

type Bucket {
  guid: ID!
  name: String!
  totalAmount: Float!
  receiptCount: Int!
  receipts(months: [String!]): [Receipt!]!
}

type Receipt {
  guid: ID!
  vendor: String!
  total: Float!
  date: String!
  timezone: String!
  notes: String!
  hash: String!
  reference: String!
  allocations: [Allocation!]!
}

type Allocation {
  amount: Float!
  bucket: Bucket!
}

type Dashboard {
  buckets: [BucketSummary!]!
  unallocated: [Receipt!]!
}

type BucketSummary {
  guid: ID!
  name: String!
  totalAmount: Float!
  receiptCount: Int!
}

type FileInfo {
  hash: String!
  filename: String!
  alreadyExists: Boolean!
}

input ReceiptInput {
  vendor: String!
  total: Float!
  date: String!
  timezone: String!
  notes: String
  hash: String
  reference: String
  allocations: [AllocationInput!]
}

input AllocationInput {
  bucketGuid: ID!
  amount: Float!
}
```

**`backend/api/graphql_server.py`**: Flask app with Ariadne.
Resolvers call existing `command.execute()` handlers exactly as today.
Domain entities (`Vendor`, `Receipt`, `Bucket`) are returned directly from resolvers —
Ariadne maps attributes by name. Only computed fields (e.g. `Vendor.receipts`) need
explicit field resolvers.

The `require_auth` decorator is adapted for the single `/graphql` route (all operations
share one HTTP endpoint).

---

### Phase 7 — Frontend: Apollo Client

Replace `src/api/client.ts` (Connect-RPC) with an Apollo Client instance.

```ts
// src/api/client.ts
import { ApolloClient, InMemoryCache, createHttpLink } from '@apollo/client'
import { setContext } from '@apollo/client/link/context'

const httpLink = createHttpLink({ uri: '/graphql' })

const authLink = setContext((_, { headers }) => ({
  headers: {
    ...headers,
    authorization: `Bearer ${localStorage.getItem('taxos_token') ?? ''}`,
  },
}))

export const client = new ApolloClient({
  link: authLink.concat(httpLink),
  cache: new InMemoryCache(),
})
```

**Frontend codegen** (`codegen.yml`):
```yaml
schema: http://localhost:50051/graphql
documents: src/**/*.graphql
generates:
  src/api/generated.ts:
    plugins:
      - typescript
      - typescript-operations
      - typescript-react-apollo
```

Run `graphql-codegen` after any schema change to regenerate typed hooks.
Replace all `useContext(TaxosContext)` API calls with `useQuery` / `useMutation` hooks.

**Vite proxy**: change from `/taxos.v1.*` to `/graphql`.

---

### Phase 8 — Export / import tools

**`backend/taxos/tenant/export/command.py`**: new scaf-callable command.
Dumps all nodes + relationships for a tenant to a JSON file.

```python
@dataclass
class ExportTenant:
    path: str = ""   # output file; defaults to stdout

    def execute(self):
        from taxos.tenant.export.handler import handle
        return handle(self)
```

Handler runs:
```cypher
MATCH (n) OPTIONAL MATCH (n)-[r]->(m) RETURN n, r, m
```
and serialises to the same JSON shape as the old `state.json` files.

**`backend/taxos/tenant/import_/command.py`**: reads that JSON and runs
`MERGE` statements to restore. Useful for seeding dev environments and
migrating existing data.

---

### Phase 9 — Cleanup (after all phases verified)

Delete:
- `proto/` directory
- `backend/api/v1/` (generated protobuf Python)
- `frontend/src/api/v1/` (generated protobuf TypeScript)
- `backend/api/connect_http_server.py`
- `backend/taxos/*/repo/` subtrees (bucket, vendor, receipt)
- `backend/taxos/tools/json.py` (custom JSON serialiser — no longer needed)
- `backend/taxos/receipt/tools.py`, `bucket/tools.py`, `vendor/tools.py` (get_state_file helpers)
- `backend/taxos/tenant/tools.py` (filesystem path helpers)
- `.scaf/dev.proto.gen` alias

Remove from `requirements.txt`: `grpcio`, `grpcio-tools`, `protobuf`

---

## Test migration

E2E test fixture (`test/fixtures.ts`) stays structurally identical:
```ts
// Before:  execSync(`${SCAF}/taxos/tenant/create "E2E Flow Test"`)  ← creates directory
// After:   same command                                              ← creates Neo4j DB
// Before:  execSync(`${SCAF}/taxos/tenant/delete "${tenantGuid}"`)  ← rm -rf
// After:   same command                                             ← DROP DATABASE
```

The fixture shell commands do not change. Only the handlers behind them change.

Backend unit/integration tests: swap any assertions that check file existence
for assertions on `db.query(...)` results against the test tenant's database.
The `--run-integration` pytest flag pattern is preserved.

---

## Sequence summary

```
Phase 0  docker-compose + db.py                         (no behaviour change)
Phase 1  Tenant entity + create/delete/load handlers    (tenant lifecycle)
Phase 2  Bucket handlers                                (no relationships)
Phase 3  Vendor handlers                                (MERGE pattern)
Phase 4  Receipt handlers + save + dashboard            (relationships)
Phase 5  Ariadne schema + graphql_server.py             (new API layer)
Phase 6  Frontend Apollo Client + codegen               (replace Connect-RPC)
Phase 7  Export / import tools                          (data portability)
Phase 8  Delete protobuf, repo layers, file-path tools  (cleanup)
```

Each phase is independently deployable and testable. Phases 0–4 can be done while
the old Connect-RPC server is still running (handlers are called the same way by scaf).
The API layer (Phase 5) and frontend (Phase 6) are switched over together.