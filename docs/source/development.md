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

```
scwgw dev config
make test-int
```

## Healthchecks

When the gateway is deployed on Scaleway Containers, Knative will perform health checks on the root path `/`. We have defined a route to handle those calls which specifically only match Knative probes `User-Agent` with the regex `~*kube-probe/.+`.

Previously, we did not specifiy a header to match against, which caused issues because in Kong every route matches `/` (routing is _greedy_). Therefore, every route which failed to match against the Gateway would be redirected to the health check and return a `200` HTTP status instead of `404`.

## Releasing

To release a new version of the CLI and gateway, we need to create an push a new tag. To do this:

```
# Bump the version
cd cli
poetry version patch

# Commit and push

# Create and push the tag
cd ..
./scripts/tag.sh
```

This will trigger the [Github Actions build](https://github.com/scaleway/serverless-gateway/actions/runs) that will build and push the container and the PyPI package.
