# Deployment

The Scaleway Gateway can be deployed on your Scaleway account using the `scwgw` utility. As it is an early access product, it is not yet available in the Scaleway CLI. However, the interface is kept as close as possible to the familiar Scaleway CLI interface.

## Prerequisites

- A Scaleway [account](https://console.scaleway.com/)
- A configured [Scaleway CLI](https://github.com/scaleway/scaleway-cli/blob/master/docs/commands/config.md).

To bootstrap the Scaleway CLI and create a config file you can run the following command:

```console
scw init
```

Alternatively, you can configure `scwgw` using the following environment variables:

- `SCW_ACCESS_KEY`
- `SCW_SECRET_KEY`
- `SCW_DEFAULT_PROJECT_ID`
- `SCW_DEFAULT_ORGANIZATION_ID`

To configure the Scaleway profile use during the deployment you can use the `SCW_PROFILE` environment variable or the `--profile` flag on the CLI.

## Installation

To deploy the gateway, you can run the following command:

```console
scwgw infra deploy
```

This deploy the gateway on your configured Scaleway Project. The deployment will take a few minutes. At the end of the deployment, the CLI will display a summary with the URL of the gateway.

## Configuration

The deployment will generate a configuration file in `$HOME/.config/scw/gateway.yml`. This file contains the configuration of the gateway, and will be used by the CLI to manage it.

The configuration file can also be generated using the following command:

```console
scwgw infra config
```

The specific deployment parameters were set by default to work well for most use cases. However, you can change them if you want to customize your deployment by configuring your containers and database with the Scaleway Console.

## Uninstalling

To uninstall the gateway, you can run the following command:

```console
scwgw infra delete
```
