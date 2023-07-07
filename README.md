# Scaleway Serverless Gateway :spider_web:

[![PyPI version](https://badge.fury.io/py/scw-gateway.svg)](https://badge.fury.io/py/scw-gateway)
[![Documentation Status](https://readthedocs.org/projects/serverless-gateway/badge/?version=latest)](https://serverless-gateway.readthedocs.io/en/latest/?badge=latest)
[![Build status](https://github.com/scaleway/serverless-gateway/actions/workflows/build.yml/badge.svg)](https://github.com/scaleway/serverless-gateway/actions/workflows/build.yml/badge.svg)

The Scaleway Serverless Gateway is a self-hosted API gateway that runs on Scaleway [Serverless Containers](https://www.scaleway.com/en/serverless-containers/).

It lets you manage routing from a single base URL, as well as handle transversal concerns such as CORS and authentication.

It is built on [Kong Gateway](https://docs.konghq.com/gateway/latest/), giving you access to the [Kong plugin ecosystem](https://docs.konghq.com/hub/) to customize your own deployments.

## :page_with_curl: Contents

- [:rocket: Features](#rocket-features)
- [:computer: Quick-start](#computer-quick-start)
- [:mortar\_board: Contributing](#mortar_board-contributing)
- [:mailbox: Reach Us](#mailbox-reach-us)

Please see [the docs](https://serverless-gateway.readthedocs.io) for full documentation and features.

## :computer: Quick-start

To deploy your gateway you need to install and configure the [Scaleway CLI](https://github.com/scaleway/scaleway-cli), and the [Gateway CLI](https://pypi.org/project/scw-gateway/) via [`pip`](https://pip.pypa.io/en/stable/index.html):

```console
pip install scw-gateway
```

Once done, the following steps can be run from the root of the project, and will deploy the gateway as a Serverless Container in your Scaleway account.

The gateway image itself is packaged via our public [Serverless Gateway Docker image](https://hub.docker.com/r/scaleway/serverless-gateway).

### Deploy your gateway

To deploy your gateway, you can run:

```console
scwgw infra deploy
```

### Add a route

To check your gateway is working, you can add and remove a route:

```console
# Check no routes are configured initially
scwgw route ls

# Check the response directly from a given URL
TARGET_URL=http://worldtimeapi.org/api/timezone/Europe/Paris
curl $TARGET_URL

# Add a route to this URL in your gateway
scwgw route add /time $TARGET_URL

# List routes to see that it's been configured
scwgw route ls

# Curl the URL via the gateway
GATEWAY_ENDPOINT=$(scwgw infra endpoint)
curl https://${GATEWAY_ENDPOINT}/time
```

### Delete your gateway

To delete your gateway, you can run:

```console
scwgw infra delete
```

## :mortar_board: Contributing

We welcome all contributions to our open-source projects, please see our [contributing guidelines](./.github/CONTRIBUTING.md).

Do not hesitate to raise issues and pull requests we will have a look at them.

## :mailbox: Reach us

We love feedback. Feel free to:

- Open a [Github issue](https://github.com/scaleway/serverless-functions-python/issues/new)
- Send us a message on the [Scaleway Slack community](https://slack.scaleway.com/), in the [#serverless-functions](https://scaleway-community.slack.com/app_redirect?channel=serverless-functions) channel.
