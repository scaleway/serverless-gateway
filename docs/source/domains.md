# Custom domains

Instead of using the default domain assigned to your gateway, you can add your own custom domains.

You can use domains you already own, or register new ones (e.g. via the Scaleway [Domains and DNS](https://www.scaleway.com/en/docs/network/domains-and-dns/quickstart/) service).

## Configuring your domain

Configuring domains is done via a [Serverless Container custom domain](https://www.scaleway.com/en/docs/serverless/containers/how-to/add-a-custom-domain-to-a-container/).

To add a domain to your gateway:

1. Add a CNAME record from your domain that points to your gateway endpoint
2. Run the CLI command `scwgw domain add <hostname of CNAME record>`

### Example

Start by getting the default endpoint for your gateway (this will be the target of the CNAME):

```
scwgw infra endpoint
```

This gives an output of the form `scwslsgwiaytodoc-scw-sls-gw.functions.fnc.fr-par.scw.cloud`.

If your domain is `my-domain.com`, you can add a new CNAME record in your DNS provider that points to your gateway, e.g. `gateway.my-domain.com`:

```
CNAME     gateway.my-domain.com     scwslsgwiaytodoc-scw-sls-gw.functions.fnc.fr-par.scw.cloud
```

Once this has been propagated, you can add the domain to your gateway with:

```
scwgw domain add gateway.my-domain.com
```

You can then check the status of your gateway domains with:

```
scwgw domain ls
```

Once the status of the domain is `ready`, all routes on your gateway will be accessible via `gateway.my-domain.com`.
