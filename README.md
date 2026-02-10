# Taxos

## Dev Commands

Discover commands:

```bash
source .venvrc
```

Run via alias:

```bash
dev.action-name plus args and --flags
```

Run directly (from repo root):

```bash
scaf . --call path/to/action/dir -- plus args and --flags
```

## Testing

From local, with devcontainers running:

### Frontend

```bash
docker exec -it taxos-frontend-1 npm run test:integration
```
