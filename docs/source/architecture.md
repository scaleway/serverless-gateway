# Architecture

The gateway is deployed using a number of Scaleway resources, all run in your Scaleway account.

The gateway itself is an instance of [Kong Gateway](https://konghq.com/), which we package in [a Docker image on Docker Hub](https://hub.docker.com/r/scaleway/serverless-gateway).

The following services are used to run the gateway:

- [Serverless Containers](https://www.scaleway.com/en/serverless-containers/) - two containers are used to run Kong, one is a private container which exposes the Kong Admin API (behind token-based auth), and the other is a public container for the Kong Gateway nodes. The Kong Gateway container has auto-scaling enabled, so more instances will be created in response to increased load.
- [Managed Databases (Postgres)](https://www.scaleway.com/en/database/) - a single managed database instance is used to run the Kong database. This is how the different Kong nodes communicate with each other, and where the gateway configuration is stored. You can read more in [the Kong traditional mode docs](https://docs.konghq.com/gateway/3.3.x/production/deployment-topologies/traditional/).
- [Secret Manager](https://www.scaleway.com/en/secret-manager/) - Secret Manager is used to share the database credentials between containers.
- [Observability Cockpit](https://www.scaleway.com/en/cockpit/) - the Kong Gateway nodes forward metrics to Cockpit using `statsd`, while Cockpit also captures all the logs from the underlying Serverless Containers.

The Kong plugins used are:

- [`jwt`](https://docs.konghq.com/hub/kong-inc/jwt/) - used to add JWT auth to routes (see [](./auth.md))
- [`cors`](https://docs.konghq.com/hub/kong-inc/jwt/) - used to add CORS headers to responses from routes (see [](./cors.md))
- [`statsd`](https://docs.konghq.com/hub/kong-inc/statsd/) - used to export metrics from gateway nodes to the Scaleway Cockpit

You can see an architecture diagram with more explanation in our [blog post](https://www.scaleway.com/en/blog/api-gateway-early-access/).
