# Scaleway Serverless Gateway :door:

Serverless Gateway is a self-hosted gateway for use in building larger serverless applications. It enables you manage different function and container URLs in a handy and intuitive manner.

## :page_with_curl: Summary

- [Quick-start](#quick-start)
    - [Export required environment variables](#Export-required-environment-variables)
    - [Create a namespace for your container](#Create-a-namespace)
    - [Create a bucket where authentication keys will be uploaded](#Create-a-bucket)
    - [Create and deploy your serverless gateway](#create-and-deploy-your-serverless-gateway)
    - [Deploy your function](#deploy-your-function)
    - [Generate an authentication key](#Generate-an-authentication-key)
    - [List generated authentication keys](#List-generated-authentication-keys)
    - [Add a function as a target in your gateway](#add-a-function-as-a-target-in-your-gateway)
    - [List the endpoints of your gateway](#list-the-endpoints-of-your-gateway)
    - [Call your function using gateway base URL](#call-your-function-using-gateway-base-url)
    - [Delete a target in your gateway](#delete-a-target-in-your-gateway)
    - [Cleanup](#Cleanup)
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

You can then follow the next steps from the root of the project to deploy the gateway as a serverless container in your Scaleway account using our public [Serverless Gateway image](https://hub.docker.com/r/shillakerscw/scw-sls-gw).

### Export required environment variables
```
vi sls-api-gw-env
source sls-api-gw-env
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
make generate-object-config
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

### Deploy your function
You can use the functions in the handler at `endpoints/func-example` and deploy it using Scaleway's Serverless API framework using:
```
scw-serverless deploy endpoints/func-example/handler.py
```
You will get two URLs, one for `hello` function and the other one for `goodbye` function.

### Generate an authentication key
```
curl -X POST http://<your container domain name>/auth
```
The generated key will be uploaded to your bucket.

You will need this key to authenticate against all `/scw` calls

### List generated authentication keys
```
make list-auth-keys
```

### Add a function as a target in your gateway
You can add `hello` function to the deployed gateway using:
```
curl -X POST http://<your container domain name>/scw -H 'Content-Type: application/json' -d '{"target":"<your hello function URL>","relative_url":"/hello"}'
```
You can add as many endpoints as you want to your serverless gateway.

### List the endpoints of your gateway
```
curl http://<your container domain name>/scw -H 'X-Auth-Token: <generated_key>' | jq
```

### Call your function using gateway base URL
```
curl http://<your container domain name>/hello
```

### Delete a target in your gateway
You can remove `hello` function as a target from your gateway using:
```
curl -X DELETE http://<your container domain name>/scw -H 'X-Auth-Token: <generated_key>' -H 'Content-Type: application/json' -d '{"target":"<your hello function URL>,"relative_url":"/hello"}'
```

### Cleanup
```
make clean-namespace
make clean-bucket
```

## :rocket: Features

Serverless Gateway is engineered to provide our clients with a better experience when using functions and containers:
* It provides you with access to multiple functions and containers via relative URLs on a single base URL. 
* It enables you direct traffic to different functions and containers based on HTTP method.
* :soon: (WIP) It allows CORS handling to make functions and containers accessible from the browser

It uses [Kong](https://konghq.com/) under the hood and is deployed as a [Serverless Container](https://www.scaleway.com/en/serverless-containers/), which acts as the proxy for other containers and functions.

It integrates fully with the [Scaleway Python API framework](https://github.com/scaleway/serverless-api-project).

## :hammer: Architecture

The gateway image is held in Docker Hub [here](https://hub.docker.com/r/shillakerscw/scw-sls-gw).

This image contains:

- The Kong gateway running in DB-less mode.
- A plugin exposing an `/auth` endpoint for authentication
- A plugin exposing an `/scw` endpoint for configuring routes to functions and containers as shown in the quick-start.

### Authentication
Via the `/auth` endpoint on the container, we can generate authentication key(s) to authenticate against `/scw` calls.

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