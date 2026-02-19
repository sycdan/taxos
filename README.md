# Taxos

It is assumed that all work will be done within the devcontainer, not on your local host machine.

## Development

**Note:** On Windows, you'll need to copy [env.example](env.example) to `.env` and update it based on the instructions inside.

### Quick Start

- Install the Dev Containers VSCode extension: `ms-vscode-remote.remote-containers`
- From the palette, select: `Dev Containers: Reopen in Container`

The frontend will be running on port 5173.

A dev tenant will be created along with the dev container, and your access token is in `./backend/data/access_tokens`.

### Dev Commands

Aliases are available for [scaf](http://scaf.sycdan.com) commands within the devcontainer (sourced from `.venvrc`).

```bash
# Reset data
dev.seed [--nuke]

# Make classes from proto
dev.proto.gen
```

You can also run them directly (from repo root):

```bash
scaf call path/to/action/dir plus args --flags
```

Scaf will create a called action if it does not exist.

## Testing

```bash
# Run all tests (unit & integration, backend & frontend):
dev.test

# Run a specific unit test:
dev.test time --no-integration
```

It is possible to debug either backend tests or endpoint hits via VSCode launch commands:

**.vscode/launch.json:**

```json
{
	"version": "0.2.0",
	"configurations": [
		{
			"name": "Backend: Attach Debugger",
			"preLaunchTask": "backend-debug",
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
			"args": ["call", "dev/test", "happy"],
			"env": {
				"PYTHONPATH": "${workspaceFolder}"
			},
			"justMyCode": false,
			"console": "integratedTerminal"
		}
	]
}
```

**.vscode/tasks.json:**

```json
{
	"tasks": [
		{
			"label": "backend-debug",
			"type": "shell",
			"command": "docker compose up backend-debug -d --force-recreate",
			"problemMatcher": []
		}
	]
}
```