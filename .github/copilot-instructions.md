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

Generate aliases:

```bash
source .venvrc
```

Use `scaf` to invoke domain actions (command.py or query.py) from the workspace root:

```bash
scaf . --call dev/action/dir -- action args
```

Or inside the backend container: (if scaf in installed there manually)

```bash
docker exec -it taxos-backend-1 scaf . -- call taxos/action/dir -- action args
```
