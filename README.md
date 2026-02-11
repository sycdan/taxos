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

Run a specific test in docker with verbose logging:

```bash
docker exec -it taxos-frontend-1 npm run test:integration -- --reporter=verbose -t "allocation"
```
