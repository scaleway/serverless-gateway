# Scaleway Serverless Gateway :door:

The Scaleway Serverless Gateway is a self-hosted API gateway that runs on Scaleway [Serverless Containers](https://www.scaleway.com/en/serverless-containers/).

It lets you manage routing from a single base URL, as well as handling transversal concerns such as CORS and authentication.

It is built on [Kong Gateway](https://docs.konghq.com/gateway/latest/), giving you access to the [Kong plugin ecosystem](https://docs.konghq.com/hub/) to customise your own deployments.

## :page_with_curl: Summary

- [Features](#rocket-features)
- [Quick-start](#computer-quick-start)
- [Custom domains](#custom-domains)
- [Serverless functions](#serverless-functions)
- [Architecture](#hammer-architecture)
- [Contributing](#mortar_board-contributing)
- [Reach Us](#mailbox-reach-us)

## :rocket: Features

The Serverless Gateway:

* Adds routing via a single base URL
* Adds routing based on HTTP methods
* Adds permissive CORS by default, to support accessing routes from a browser

The Serverless Gateway integrates fully with the [Scaleway Python API framework](https://github.com/scaleway/serverless-api-project), which makes building and managing complex serverless APIs easy.

## :computer: Quick-start

Before deploying your gateway you need to install the following:

- The [Scaleway CLI](https://github.com/scaleway/scaleway-cli)
- [`jq`](https://stedolan.github.io/jq/download/) for parsing JSON responses
- [`s3cmd`](https://github.com/s3tools/s3cmd/blob/master/INSTALL.md) for interacting with [Scaleway Object Storage](https://www.scaleway.com/en/object-storage/)
- `make` for running commands via the project `Makefile`

Once done, the following steps can be run from the root of the project, and will deploy the gateway as a Serverless Container in your Scaleway account.

The gateway is packaged via our public [Serverless Gateway Docker image](https://hub.docker.com/r/scaleway/serverless-gateway).

*1. Provide your Scaleway credentials*

You will need to set your Scaleway access and secret keys in the `gateway.env` file:

```
SCW_ACCESS_KEY=<your access key>
SCW_SECRET_KEY=<your secret key>
```

*2. Create a bucket to store tokens*

The gateway needs to generate and store your access tokens in a bucket, which can be created by running:

```
make set-up-s3-cli
make create-s3-bucket
```

*3. Deploy your gateway*

To deploy your gateway, you need to create a container namespace, and a container in that namespace using the public gateway image:

```
# Create the namespace
make create-namespace

# Wait for the namespace to be ready
make check-namespace

# Create and deploy the container
make create-container deploy-container

# Check the status of your container
make check-container
```

*4. Generate a token*

```
# Generate a token which is written to your private S3 bucket
make generate-token

# Retrieve the token
make get-token
```

The generated token will be used to authenticate against all calls that modify the gateway.

*5. Add a route*

You can add a route to any URL, here we will use the `worldtimeapi`.

```
# Curl the URL directly
curl http://worldtimeapi.org/api/timezone/Europe/Paris

# Set up gateway params
export TOKEN=$(make get-token)
export GATEWAY_HOST=$(make gateway-host)

# Add route on the gateway
curl -X POST http://${GATEWAY_HOST}/scw \
             -H "X-Auth-Token: ${TOKEN}" \
             -H 'Content-Type: application/json' \
             -d '{"target":"http://worldtimeapi.org/api/timezone/Europe/Paris","relative_url":"/time"}'

# Now curl through your gateway
curl http://${GATEWAY_HOST}/time
```

*6. List routes*

You can list the routes configured on your gateway with:

```
make list-routes
```

### Updating your gateway

If you make changes to your gateway in this repo, you can run the following to update it:

```
# Update without redeploy
make update-container-without-deploy

# Update with redeploy
make update-container
```

### Deleting your gateway

To clear up everything related to your gateway, you can run:

```
# Delete the namespace, which implicitly deletes the container
make delete-namespace

# Delete the bucket used to store tokens
make delete-bucket
```

## Custom domains

You can add a custom domain to your gateway as with any other Serverless Container.

You can register a new domain as described in the [Domains and DNS docs](https://www.scaleway.com/en/docs/network/domains-and-dns/quickstart/).

Then you can add your domain name as global variable to the makefile:

```
GATEWAY_CUSTOM_DOMAIN := your-custom-domain-name
```

Then uou can add your domain name to your gateway using:

```
make set-custom-domain
```

## Serverless functions

Serverless Functions and Containers can be added to your gateway as a route just like any other URL.

You can try this using the function included at `endpoints/func-example`.

This function uses [Scaleway's Python Serverless API Framework](https://github.com/scaleway/serverless-api-project), which must be installed for the example to work.

Once set up, you can deploy the functions with:

```
scw-serverless deploy endpoints/func-example/handler.py
```

This will create two URLs, one for the `hello` function and the other one for the `goodbye` function.

## :hammer: Architecture

The gateway is packaged via [a public Docker image on Docker Hub](https://hub.docker.com/r/scaleway/serverless-gateway).

This image contains:

- The Kong gateway
- A plugin exposing an `/token` endpoint for generating tokens
- A plugin exposing an `/scw` endpoint for configuring routes

### Authentication

Using the `/token` endpoint on the gateway, we can generate tokens to authenticate against `/scw` calls.

The generated tokens are uploaded to a private bucket configured using the parameters in the `gateway.env` file.

### Configuring routes

The `/scw` endpoint allows us to add and remove routes without having to redeploy the gateway and interrupt service.

Routes has the following fields:

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
