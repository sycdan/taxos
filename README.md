# Taxos

It is assumed that all work will be done within the devcontainer, not on your local host machine.

## Development

### Quick Start

- Install the Dev Containers VSCode extension: `ms-vscode-remote.remote-containers`
- From the palette, select: `Dev Containers: Reopen in Container`

### Dev Commands

Aliases are available for Scaf commands within the devcontainer (sourced from `.venvrc`).

You can also run them directly (from repo root):

```bash
scaf . --call path/to/action/dir -- plus args and --flags
```

### Adding Actions

```bash
scaf.create-action path/to/new/action
```

## Testing

```bash
dev.test
```
