# To Do: Taxos Development

## Today's Task

We need to work on the dev environment, which is flaky right now.

We tried using devcontainers with a lof of customizations and features, but it's cumbersome and too tightly coupled to vscode.

We can still use the devconatiner extension, but we'd like to build a custom devcontainer that does not rely in the vscode extensions (e.g. the oncreate hook) to bootstrap. We should make its dockerfile more inclusive.

We would like to be able to run docker compose up on the host, and then docker exec bash on the dev container to get to a working environment.

We need python debugging to work flawlessly, using a modern approach (e.g. sidecar), and be able to debug against the production app container. We also need hot reloading (can be managed using docker compose develop settings, I believe).

You need to show me everything working.

### Rules

- do not install python packages on my local system
  - we need to keep dependencies isolated in the dev and/or sidecar containers
- do not include or require debugpy in the production backend image build
- the dev container should be usable (bootstrapped) without vscode

