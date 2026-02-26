> [!WARNING]
> **Project Deprecated**
>
> This project is deprecated and will soon be replaced by **Scaleway Edge Services**, a fully managed API gateway solution compatible with Serverless Functions and Serverless Containers.
>
> Scaleway Edge Services will provide enhanced features, better performances, and seamless integration with the Scaleway ecosystem. The product is expected to be released soon.

# <img src="https://raw.githubusercontent.com/scaleway/serverless-gateway/main/logo.png" height="32"/> Scaleway Serverless Gateway

[![PyPI version](https://badge.fury.io/py/scw-gateway.svg)](https://badge.fury.io/py/scw-gateway)
[![Documentation Status](https://readthedocs.org/projects/serverless-gateway/badge/?version=latest)](https://serverless-gateway.readthedocs.io/en/latest/?badge=latest)
[![Build status](https://github.com/scaleway/serverless-gateway/actions/workflows/build.yml/badge.svg)](https://github.com/scaleway/serverless-gateway/actions/workflows/build.yml/badge.svg)

The Scaleway Serverless Gateway is a self-hosted API gateway that runs on Scaleway [Serverless Containers](https://www.scaleway.com/en/serverless-containers/).

It lets you manage routing from a single base URL, as well as handling transversal concerns such as CORS and authentication.

It is built on [Kong Gateway](https://docs.konghq.com/gateway/latest/), giving you access to the [Kong plugin ecosystem](https://docs.konghq.com/hub/) to customize your deployments.

You can read all about it in [this blog post](https://www.scaleway.com/en/blog/api-gateway-early-access/).

If you would like to join in the discussion on how we continue developing the project, or give us feedback, then join us on the [#api-gateway-beta](https://app.slack.com/client/T7YEXCR7X/C05H07VBKJ4) channel on the Scaleway Community Slack.

## 📃 Contents

<!-- no toc -->
- [Scaleway Serverless Gateway](#-scaleway-serverless-gateway)
  - [📃 Contents](#-contents)
  - [💻 Quickstart](#-quickstart)
    - [Deploy your gateway](#deploy-your-gateway)
    - [Add a route](#add-a-route)
    - [Delete your gateway](#delete-your-gateway)
  - [🎓 Contributing](#-contributing)
  - [📬 Reach us](#-reach-us)
<!-- no toc -->

Please see [the docs](https://serverless-gateway.readthedocs.io) for full documentation and features.

## 💻 Quickstart

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

For more information on the deployment process, see the [deployment docs](https://serverless-gateway.readthedocs.io/en/latest/deployment.html).

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

## 🎓 Contributing

We welcome all contributions to our open-source projects, please see our [contributing guidelines](./.github/CONTRIBUTING.md).

Do not hesitate to raise issues and pull requests we will have a look at them.

## 📬 Reach us

We love feedback. Feel free to:

- Open a [Github issue](https://github.com/scaleway/serverless-gateway/issues/new)
- Send us a message on the [Scaleway Slack community](https://slack.scaleway.com/), in the [#serverless-functions](https://scaleway-community.slack.com/app_redirect?channel=serverless-functions) channel.
