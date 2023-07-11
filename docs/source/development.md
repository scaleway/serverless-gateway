# Development

## Getting started

To get started with development, you need to set up a Python environment with [Poetry](https://python-poetry.org/docs/).

First of all, you need to launch the gateway locally:

```console
cd gateway
docker compose up
```

Then from the root of the project, you can launch the CLI:

```console
cd cli
poetry shell
poetry install
```

Inside your poetry shell, you can generate the config and launch the integration tests locally:

```console
scwgw dev config
make test-int
```

## Updating the gateway

After making changes to the underlying containers, you can run the following to update your deployment:

```console
scwgw dev update-containers
```

## Observability

The settings for metrics collection can be configured using the following environment variables on your containers:

<!-- markdownlint-disable MD033 -->
| Variable                  | Description                      | Default |
|---------------------------|----------------------------------|---------|
| `METRICS_SCRAPE_INTERVAL` | Time interval to scrape metrics. | 15s     |
| `COCKPIT_METRICS_PUSH_URL` | Cockpit push metrics endpoint. <br/>Can be found on the Cockpit console page.                           |         |
| `COCKPIT_METRICS_TOKEN`    | Cockpit metrics push token.  <br/> Requires the `write_metrics` scope.                                 |         |

## Releasing

To release a new version of the CLI and gateway, we need to create an push a new tag. To do this:

```console
# Bump the version
cd cli
poetry version patch

# Commit and push

# Create and push the tag
cd ..
./scripts/tag.sh
```

This will trigger the [Github Actions build](https://github.com/scaleway/serverless-gateway/actions/runs) that will build and push the container and the PyPI package.
