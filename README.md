# Taxos

It is assumed that all work will be done within the devcontainer, not on your local host machine.

## Development

### Quick Start

- Install the Dev Containers VSCode extension: `ms-vscode-remote.remote-containers`
- From the palette, select: `Dev Containers: Reopen in Container`

The frontend will be running on port 5173.

A dev tenant will be created along with the dev container, and your access token is in `./backend/data/access_tokens`.

### Dev Commands

Aliases are available for Scaf commands within the devcontainer (sourced from `.venvrc`).

```bash
dev.seed
```

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
# Run all tests (unit & integration, backend & frontend):
dev.test

# Run a specific unit test:
dev.test time --no-integration
```

It is possible to debug either backend tests or endpoint hits via VSCode launch commands:

```json
{
	"version": "0.2.0",
	"configurations": [
		{
			"name": "Backend: Attach Debugger",
			"type": "debugpy",
			"request": "attach",
			"connect": {
				"host": "localhost",
				"port": 5678
			},
			"pathMappings": [
				{
					"localRoot": "${workspaceFolder}",
					"remoteRoot": "/workspaces/taxos"
				}
			],
			"justMyCode": false
		},
		{
			"name": "Dev: Test Domain",
			"type": "debugpy",
			"request": "launch",
			"module": "scaf",
			"args": ["${workspaceFolder}", "--call=dev/test", "--", "happy"],
			"env": {
				"PYTHONPATH": "${workspaceFolder}"
			},
			"justMyCode": false,
			"console": "integratedTerminal"
		}
	]
}
```
