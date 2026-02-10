# Taxos

Receipt and bucket management system.

## Development

### Backend

- python, connectrpc, protobuf, scaf
- Docker container: taxos-backend-1
- Port: 50051 (connectrpc)
- API definitions in `proto/v1/taxos_service.proto`
- Domain: tenants, receipts, buckets
- Auth: custom tokens (identifying a Tenant)
- Tenant data stored in `backend/data/tenants/`

### Frontend

- react, vite, typescript, connectrpc
- Docker container: taxos-frontend-1
- Port: 5173
- Connects to backend API via Connect-RPC

### Dev Commands

Use `scaf` command system (source `.venvrc` to enable aliases):

- `domain.action-name` or `scaf . --call path/to/action/dir`
- Common: dev.serve, dev.gen-proto
