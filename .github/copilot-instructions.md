# Taxos

Receipt and bucket management system.

## Development

### Backend

- python, GraphQL, scaf
- Docker container: taxos-backend-1
- Port: 50052 (GraphQL)
- Domain: tenants, receipts, buckets
- Auth: custom tokens (identifying a Tenant)
- Tenant data stored in `backend/data/tenants/`

### Frontend

- react, vite, typescript
- Docker container: taxos-frontend-1
- Port: 5173
- Connects to backend API via GraphQL

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
