# Scaleway Serverless API Gateway

This is a self-hosted gateway for use in building larger serverless applications.

## Quick-start

To get started with the gateway, you must do the following:

- Install and configure the [Scaleway CLI](https://github.com/scaleway/scaleway-cli)
- Install [`jq`](https://stedolan.github.io/jq/download/)
- Install [`Scaleway's Serverless API Framework`](https://github.com/scaleway/serverless-api-project)


You can then follow the next steps from the root of the project to deploy the gateway as a serverless container in your Scaleway account.

### Create a namespace for your container 

```
make create-namespace
make check-namespace
```

### Create a container
```
make create-container
make check-container
```

In case you want to update your container your can use:
```
make update-container
```

Get the domain name of yout container when it is ready.

### Deploy your function
You can use the functions in the handler at `endpoints/func-example` and deploy using Scaleway's Serverless API framework using:
```
scw-serverless deploy endpoints/func-example/handler.py
```

You will get two URLs, one for `hello` function and the other one `goodbye` function.


### Add a function as a target in your gateway
You can add `hello` function to the deployed gateway using:
```
curl -X POST <your container domain name>/scw -H 'Content-Type: application/json' -d '{"target":"<your hello function URL>","relative_url":"/hello"}'
```
You can add as many endpoints as you want.

### List the endpoints of your gateway
```
curl <your container domain name>/scw | jq
```

### Call your function using gateway base URL
```
curl <your container domain name>/hello
```

### Delete a target in your gateway
You can remove `hello` function as a target from your gateway using:
```
curl -X DELETE <your container domain name>/scw -H 'Content-Type: application/json' -d '{"target":"<your hello function URL>,"relative_url":"/hello"}'
```

## Features

- Access multiple functions and containers via relative URLs on a single base URL
- Direct traffic to different functions and containers based on HTTP method
- CORS handling to make functions and containers accessible from the browser

It uses [Kong](https://konghq.com/) under the hood and is deployed as a [Serverless Container](https://www.scaleway.com/en/serverless-containers/), which acts as the proxy for other containers and functions.

It integrates fully with the [Scaleway Python API framework](https://github.com/scaleway/serverless-api-project).

## Architecture

The gateway image is held in Dockerhub [here](https://hub.docker.com/r/shillakerscw/scw-sls-gw).

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

