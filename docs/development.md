# Development

## Getting started

To get started with development, you can first set up a Python virtual environment:

```
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements-dev.txt
```

Then you can try running the gateway and integration test:

```
# Start the gateway
docker compose up -d

# Check that the gateway has started
docker compose ps -a

# Run the integration test
make test-int
```

## Kong plugin

The `/scw` endpoint is managed using a custom plugin for [Kong](https://docs.konghq.com), built using the [Kong Python plugin development kit](https://github.com/Kong/kong-python-pdk).

The [Kong Python plugin docs](https://docs.konghq.com/gateway/latest/plugin-development/pluginserver/python/) and a [longer example](https://konghq.com/blog/building-plugins-for-kong-gateway-using-python) are useful reading.

