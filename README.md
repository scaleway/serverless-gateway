# Scaleway Serverless Gateway

Serverless Gateway is a self-hosted gateway for use in building larger serverless applications. It enables you manage different function and container URLs in a handy and intuitive manner.

## Quick-start

To get started with the gateway, you must do the following:

- Install and configure the [Scaleway CLI](https://github.com/scaleway/scaleway-cli).
- Install [`jq`](https://stedolan.github.io/jq/download/) system tool.
- Install [`Scaleway's Serverless API Framework`](https://github.com/scaleway/serverless-api-project).

You can then follow the next steps from the root of the project to deploy the gateway as a serverless container in your Scaleway account using our public [Serverless Gateway image](link-to-public-gw-image).

### Create a namespace for your container 
You can use:
```
make create-namespace
```

To check the status of your namespace, use the following:
```
make check-namespace
```

### Create and deploy a container to host your serverless gateway
You can use:
```
make create-container
make deploy-container
```
To check the status of your container, use the following:
```
make check-container
```
Get the domain name of your container form container description when it is ready. It is the base URL of your serverless gateway.

In case you want to update your container, you can use:
```
make update-container
```

### Deploy your function
You can use the functions in the handler at `endpoints/func-example` and deploy it using Scaleway's Serverless API framework using:
```
scw-serverless deploy endpoints/func-example/handler.py
```
You will get two URLs, one for `hello` function and the other one for `goodbye` function.

### Add a function as a target in your gateway
You can add `hello` function to the deployed gateway using:
```
curl -X POST http://<your container domain name>/scw -H 'Content-Type: application/json' -d '{"target":"<your hello function URL>","relative_url":"/hello"}'
```
You can add as many endpoints as you want to your serverless gateway.

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
curl -X DELETE http://<your container domain name>/scw -H 'Content-Type: application/json' -d '{"target":"<your hello function URL>,"relative_url":"/hello"}'
```

## Features

Serverless Gateway is engineered to provide our clients with a better experience when using functions and containers. This solution provides you with access to multiple functions and containers via relative URLs on a single base URL. It enables you direct traffic to different functions and containers based on HTTP method.

It uses [Kong](https://konghq.com/) under the hood and is deployed as a [Serverless Container](https://www.scaleway.com/en/serverless-containers/), which acts as the proxy for other containers and functions.

It integrates fully with the [Scaleway Python API framework](https://github.com/scaleway/serverless-api-project).

## Architecture

The gateway image is held in Docker Hub [here](https://hub.docker.com/r/shillakerscw/scw-sls-gw).

This image contains:

- The Kong gateway running in DB-less mode.
- A plugin exposing an `/scw` endpoint for configuring routes to functions and containers as shown in the quick-start.

### Configuring routes

Via the `/scw` endpoint on the container, we can add and remove routes to other functions and containers. This allows users to add, update, and remove routes without having to redeploy the gateway and interrupt service.

Each route has the following fields:

- `relative_url`: the relative URL on the gateway.
- `target_url`: the URL of the target function or container.
- `http_method` (optional): the HTTP methods to accept on this endpoint.
