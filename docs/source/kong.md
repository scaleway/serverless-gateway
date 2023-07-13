# Using Kong directly

The CLI offered in this project makes it possible to perform many of the common operations related to managing a Kong API Gateway.

However, for more advanced use-cases, users may need to make changes not supported by the CLI. To do this they can directly access the Kong Admin API.

The Kong Admin API lets you configure everything that Kong offers, including managing plugins from the [Kong Plugin hub](https://docs.konghq.com/hub/). To find out more, check out the [Kong Admin API docs](https://docs.konghq.com/gateway/latest/admin-api/).

## Accessing the Kong Admin API

As part of a gateway deployment, the Kong Admin API runs in a private [Scaleway Serverless Container](https://www.scaleway.com/en/serverless-containers/).

This means it uses token-based authentication, which requires passing a token with _every request_ via the `X-Auth-Token` header.

You can get your access token by running:

```console
scwgw infra admin-token
```

You can get the endpoint for the Admin API by running:

```console
scwgw infra admin-endpoint
```

## Example

A full example of making a request to the Admin API is:

```console
# Get the endpoint and token
ADMIN_ENDPOINT=https://$(scwgw infra admin-endpoint)
ADMIN_TOKEN=$(scwgw infra admin-token)

# List the routes on the gateway
curl -H "X-Auth-Token: $ADMIN_TOKEN" $ADMIN_ENDPOINT/routes
```
