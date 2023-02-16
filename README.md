# Scaleway Serverless API Gateway

This is a self-hosted gateway for use in building larger serverless applications.

Features:

- Access multiple functions and containers via relative URLs on a single base URL
- Direct traffic to different functions and containers based on HTTP method
- CORS handling to make functions and containers accessible from the browser

It uses [Kong](https://konghq.com/) under the hood and is deployed as a [Serverless Container](https://www.scaleway.com/en/serverless-containers/), which acts as the proxy for other containers and functions.

It integrates fully with the [Scaleway Python API framework](https://github.com/scaleway/serverless-api-project).

## Architecture

The gateway image is held in Dockerhub at [`scaleway/scw-sls-gw`](https://hub.docker.com/scaleway).

This image contains:

- The Kong gateway (running in DB-less mode)
- A plugin exposing an `/scw` endpoint for configuring routes to functions and containers

### Configuring routes

Via the `/scw` endpoint on the container, we can add and remove routes to other functions and containers. This allows users to add, update, and remove routes without having to redeploy the gateway and interrupt service.

Each route has the following fields:

- `relative_url` - the relative URL on the gateway
- `target_url` - the URL of the target function or container
- `http_method` (optional) - the HTTP methods to accept on this endpoint

To create a route, a client can send a `POST` request to the `/scw` endpoint, e.g. with `curl`:

```
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"relative_url":"/foo/bar","target_url":"https://<function url>"}' \
  http://<gateway host>/scw
```

