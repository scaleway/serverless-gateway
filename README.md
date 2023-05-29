# Scaleway Serverless Gateway :door:

The Scaleway Serverless Gateway is a self-hosted API gateway that runs on Scaleway [Serverless Containers](https://www.scaleway.com/en/serverless-containers/).

It lets you manage routing from a single base URL, as well as handle transversal concerns such as CORS and authentication.

It is built on [Kong Gateway](https://docs.konghq.com/gateway/latest/), giving you access to the [Kong plugin ecosystem](https://docs.konghq.com/hub/) to customize your own deployments.

## :page_with_curl: Contents

- [:rocket: Features](#rocket-features)
- [:computer: Quick-start](#computer-quick-start)
  - [Updating your gateway](#updating-your-gateway)
  - [Deleting your gateway](#deleting-your-gateway)
- [Custom domains](docs/custom-domain.md)
- [Serverless functions](docs/serverless.md)
- [:hammer: Architecture](docs/architecture.md)
- [:mortar\_board: Contributing](#mortar_board-contributing)
- [:mailbox: Reach Us](#mailbox-reach-us)

## :rocket: Features

The Serverless Gateway:

- Adds routing via a single base URL
- Adds routing based on HTTP methods
- Adds permissive CORS by default, to support accessing routes from a browser
- Gives access to a serverless [Kong Gateway](https://docs.konghq.com/gateway/latest/) deployment

The Serverless Gateway integrates fully with the [Scaleway Python API framework](https://github.com/scaleway/serverless-api-project), which makes building and managing complex serverless APIs easy.

## :computer: Quick-start

To deploy your gateway you need to install and configure the [Scaleway CLI](https://github.com/scaleway/scaleway-cli), and the [Gateway CLI](https://pypi.org/project/scw-gateway/) via [`pip`](https://pip.pypa.io/en/stable/index.html):

```console
pip install scw-gateway
```

Once done, the following steps can be run from the root of the project, and will deploy the gateway as a Serverless Container in your Scaleway account.

The gateway image itself is packaged via our public [Serverless Gateway Docker image](https://hub.docker.com/r/scaleway/serverless-gateway).

*1. Deploy your gateway*

To deploy your gateway, you need to create a container namespace, and a container in that namespace using the public gateway image:

```console
# Create the database
scwgw create-db

# Create the namespace
scwgw create-namespace

# Wait for the namespace to be ready
scwgw await-namespace

# Create and deploy the containers
scwgw create-containers

# Wait for the containers to be ready
scwgw await-containers

# Wait for the database to be ready
scwgw await-db
```

*2. Set up your config*

Configure your local CLI to use all the newly deployed resources:

```console
scwgw remote-config
```

*3. Add a route*

You can add a route to any URL, here we will use the `worldtimeapi`.

```console
# Curl the URL directly
curl http://worldtimeapi.org/api/timezone/Europe/Paris

# Set up gateway params
scwgw add-route /time http://worldtimeapi.org/api/timezone/Europe/Paris

# Now curl through your gateway
curl http://${GATEWAY_HOST}/time
```

*4. List routes*

You can list the routes configured on your gateway with:

```console
scwgw get-routes
```

### Updating your gateway

If you make changes to your gateway in this repo, you can run the following to update it:

```console
# Update without redeploy
scwgw update-container-no-redeploy

# Update with redeploy
scwgw update-container
```

### Deleting your gateway

To clear up everything related to your gateway, you can run:

```console
# Delete the namespace, which implicitly deletes the container
scwgw delete-namespace

# Delete the bucket used to store tokens
scwgw delete-bucket
```

## :mortar_board: Contributing

We welcome all contributions to our open-source projects, please see our [contributing guidelines](./.github/CONTRIBUTING.md).

Do not hesitate to raise issues and pull requests we will have a look at them.

## :mailbox: Reach Us

We love feedback. Feel free to:

- Open a [Github issue](https://github.com/scaleway/serverless-functions-python/issues/new)
- Send us a message on the [Scaleway Slack community](https://slack.scaleway.com/), in the [#serverless-functions](https://scaleway-community.slack.com/app_redirect?channel=serverless-functions) channel.
