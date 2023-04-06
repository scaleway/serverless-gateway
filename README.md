# Scaleway Serverless Gateway :door:

Serverless Gateway is a self-hosted gateway for use in building larger serverless applications. It enables you manage different function and container URLs in a handy and intuitive manner.

## :page_with_curl: Summary

- [Quick-start](#quick-start)
    - [Export required environment variables](#export-required-environment-variables)
    - [Create a namespace for your container](#create-a-namespace)
    - [Create a bucket where tokens will be uploaded](#create-a-bucket)
    - [Create and deploy your serverless gateway](#create-and-deploy-your-serverless-gateway)
    - [Deploy your function](#deploy-your-function)
    - [Generate a token](#generate-a-token)
    - [List generated tokens](#list-generated-tokens)
    - [Add a function as a target in your gateway](#add-a-function-as-a-target-in-your-gateway)
    - [List the endpoints of your gateway](#list-the-endpoints-of-your-gateway)
    - [Call your function using gateway base URL](#call-your-function-using-gateway-base-url)
    - [Delete a target in your gateway](#delete-a-target-in-your-gateway)
    - [Cleanup](#cleanup)
- [Features](#features)
- [Architecture](#architecture)
    - [Configuring routes](#configuring-routes)
- [Contributing](#contributing)
- [Reach Us](#reach-us)

## :computer: Quick-start

To get started with the gateway, you must do the following:

- Install and configure the [Scaleway CLI](https://github.com/scaleway/scaleway-cli)
- Install [`jq`](https://stedolan.github.io/jq/download/)
- Install [`Scaleway's Serverless API Framework`](https://github.com/scaleway/serverless-api-project)
- Install [`s3cmd`](https://github.com/s3tools/s3cmd/blob/master/INSTALL.md)

You can then follow the next steps from the root of the project to deploy the gateway as a serverless container in your Scaleway account using our public [Serverless Gateway image](https://hub.docker.com/r/scaleway/serverless-gateway).

### Export required environment variables
You need to provide the gateway with your S3 bucket configuration
```
vi gateway.env
```

### Create a namespace 
You can deploy your serverless gateway using a serverless container. Create a namespace for your container using:
```
make create-namespace
```

To check the status of your namespace, use the following:
```
make check-namespace
```

### Create a bucket
```
make set-up-s3-cli
make create-s3-bucket
```

### Create and deploy your serverless gateway
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

In case you want to update your container without deploying it you can use:
```
make update-container-without-deploy
```

In case you want to update your container, you can use:
```
make update-container
```

### Add gateway URL as environment variable
You can use:
```
export GATEWAY_URL=$(make get-gateway-endpoint)
```

### Deploy your function
You can use the functions in the handler at `endpoints/func-example` and deploy it using Scaleway's Serverless API framework using:
```
scw-serverless deploy endpoints/func-example/handler.py
```
You will get two URLs, one for `hello` function and the other one for `goodbye` function.

### Generate a token
```
curl -X POST http://${GATEWAY_URL}/token
```
The generated key will be uploaded to your bucket.

You will need this token to authenticate against all `/scw` calls

### List generated tokens
```
make list-tokens
```

### Add token as environment variable
You can use:
```
export GATEWAY_TOKEN=$(make get-gateway-token)
```

### Add a function as a target in your gateway
You can add `hello` function to the deployed gateway using:
```
curl -X POST http://${GATEWAY_URL}/scw \
             -H "X-Auth-Token: ${GATEWAY_TOKEN}" \
             -H 'Content-Type: application/json' \
             -d '{"target":"<your hello function URL>","relative_url":"/hello"}'
```
You can add as many endpoints as you want to your serverless gateway. 

Make sure that your endpoint targets are prefixed with `http://` or `https://`.

### List the endpoints of your gateway
```
curl http://${GATEWAY_URL}/scw -H "X-Auth-Token: ${GATEWAY_TOKEN}"| jq
```

### Call your function using gateway base URL
```
curl http://${GATEWAY_URL}/hello
```

### Delete a target in your gateway
You can remove `hello` function as a target from your gateway using:
```
curl -X DELETE http://${GATEWAY_URL}/scw \
               -H "X-Auth-Token: ${GATEWAY_TOKEN}" \
               -H 'Content-Type: application/json' \
               -d '{"target":"<your hello function URL>,"relative_url":"/hello"}'
```

### Cleanup
```
make delete-namespace
make delete-bucket
```

### Add custom domain name to gateway
You can add a custom domain name of your choice as an endpoint to your serverless gateway container. Take a look at how to register a domain name using Scaleway's `Domains and DNS` [here](https://www.scaleway.com/en/docs/network/domains-and-dns/quickstart/).
Then, you can add your domain name as global variable to the makefile:
```
CONTAINER_CUSTOM_DOMAIN := your-custom-domain-name
```
You can add your domain name to your container's endpoints using the command:
```
make add-container-endpoint
```

## :rocket: Features

Serverless Gateway is engineered to provide our clients with a better experience when using functions and containers:
* It provides you with access to multiple functions and containers via relative URLs on a single base URL. 
* It enables you direct traffic to different functions and containers based on HTTP method.
* It allows CORS handling to make functions and containers accessible from the browser

It uses [Kong](https://konghq.com/) under the hood and is deployed as a [Serverless Container](https://www.scaleway.com/en/serverless-containers/), which acts as the proxy for other containers and functions.

It integrates fully with the [Scaleway Python API framework](https://github.com/scaleway/serverless-api-project).

## :hammer: Architecture

The gateway image is held in Docker Hub [here](https://hub.docker.com/r/scaleway/serverless-gateway).

This image contains:

- The Kong gateway running in DB-less mode.
- A plugin exposing an `/token` endpoint for generating tokens
- A plugin exposing an `/scw` endpoint for configuring routes to functions and containers as shown in the quick-start.

### Authentication
Via the `/token` endpoint on the container, we can generate tokens to authenticate against `/scw` calls.

The generated key(s) will be uploaded into a bucket which its configuration is provided as secrets environment variables to the container:
```
SCW_ACCESS_KEY: <scaleway_access_key>
SCW_SECRET_KEY: <scaleway secret key>
S3_REGION:      <s3 bucket region>
S3_ENDPOINT:    <s3 endpoint url>
S3_BUCKET_NAME: <s3 bucket name>
```

### Configuring routes

Via the `/scw` endpoint on the container, we can add and remove routes to other functions and containers. This allows users to add, update, and remove routes without having to redeploy the gateway and interrupt service.

Each route has the following fields:

- `relative_url`: the relative URL on the gateway.
- `target_url`: the URL of the target function or container.
- `http_method` (optional): the HTTP methods to accept on this endpoint.

## :mortar_board: Contributing

We welcome all contributions to our open-source projects, please see our [contributing guidelines](./.github/CONTRIBUTING.md).

Do not hesitate to raise issues and pull requests we will have a look at them.

## :mailbox: Reach Us

We love feedback. Feel free to:

- Open a [Github issue](https://github.com/scaleway/serverless-functions-python/issues/new)
- Send us a message on the [Scaleway Slack community](https://slack.scaleway.com/), in the [#serverless-functions](https://scaleway-community.slack.com/app_redirect?channel=serverless-functions) channel.
