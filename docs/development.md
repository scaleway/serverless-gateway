# Development

## Getting started

To get started with development, you can first set up a Python virtual environment:

```console
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements-dev.txt
```

Then you can try running the gateway and integration test:

```console
# Start the gateway
docker compose up -d

# Check that the gateway has started
docker compose ps -a

# Run the integration test
make test-int
```

## Kong plugin

The `/auth` and `/scw` endpoints are managed using a custom plugin for [Kong](https://docs.konghq.com), built using the [Kong Python plugin development kit](https://github.com/Kong/kong-python-pdk).

The [Kong Python plugin docs](https://docs.konghq.com/gateway/latest/plugin-development/pluginserver/python/) and a [longer example](https://konghq.com/blog/building-plugins-for-kong-gateway-using-python) are useful reading.

## Healthchecks

When the gateway is deployed on Scaleway Containers, Knative will perform health checks on the root path `/`. We have defined a route to handle those calls which specifically only match Knative probes `User-Agent` with the regex `~*kube-probe/.+`.

Previously, we did not specifiy a header to match against, which caused issues because in Kong every route matches `/` (routing is _greedy_). Therefore, every route which failed to match against the Gateway would be redirected to the health check and return a `200` HTTP status instead of `404`.

## CORS support for endpoints

Each functions/container endpoint has its attached Kong built-in CORS plugin with a fixed configuration as you can see [here](../gateway/endpoint.py). You can add more plugins to the list of endpoint built-in plugins. When a new endpoint is created through the gateway, a plugin attached to service of this endpoint is generated in the plugins list. When the endpoint is deleted the attached plugin is deleted as well.
