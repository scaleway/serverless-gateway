# Development

## Getting started

To get started with development, you can first set up a Python virtual environment:

```
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements-dev.txt
```
Export required environment variables
```
export SCW_ACCESS_KEY=minioadmin
export SCW_SECRET_KEY=minioadmin
export S3_REGION=whatever
export S3_ENDPOINT=http://minio:9000
export S3_BUCKET_NAME=auth-keys
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

The `/auth` and `/scw` endpoints are managed using a custom plugin for [Kong](https://docs.konghq.com), built using the [Kong Python plugin development kit](https://github.com/Kong/kong-python-pdk).

The [Kong Python plugin docs](https://docs.konghq.com/gateway/latest/plugin-development/pluginserver/python/) and a [longer example](https://konghq.com/blog/building-plugins-for-kong-gateway-using-python) are useful reading.

