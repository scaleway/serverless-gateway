# Architecture

The gateway is packaged via [a public Docker image on Docker Hub](https://hub.docker.com/r/scaleway/serverless-gateway).

It uses the following Scaleway services to run an instance of [Kong Gateway](https://konghq.com/):

- [Serverless Containers](https://www.scaleway.com/en/serverless-containers/) - a private container to run the Kong admin, and public containers for the gateway nodes
- [Managed Databases (Postgres)](https://www.scaleway.com/en/database/) - to hold the Kong database state
- [Secret Manager](https://www.scaleway.com/en/secret-manager/) - to store the database credentials and share with containers
- [Observability Cockpit](https://www.scaleway.com/en/cockpit/) - to view metrics from the gateway using [Kong statsd](https://docs.konghq.com/hub/kong-inc/statsd/)
