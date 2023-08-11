# IAM

To deploy the gateway using Scaleway IAM, we recommend the following setup:

1. Create a new Scaleway project
2. Create an IAM application scoped to this project
3. Add a policy with this application as principal
4. Add the following rules to the policy:
    - Serverless -> `ContainersFullAccess`
    - Managed services -> `ObservabilityFullAccess`
    - Managed databases -> `RelationalDatabasesFullAccess`
    - Security and identity -> `SecretManagerFullAccess`
5. Create an API key for the application
6. Use this API key's secret key and access key when deploying your gateway (see below)

By scoping the API key to the new project, you limit the privileges of the key to resources within that project.

## Using an API key

The easiest ways to use an API key are via:

1. A profile in your Scaleway CLI config file (either set as the default, or using the `--profile` argument for the gateway CLI)
2. Environment variables, setting `SCW_ACCESS_KEY` and `SCW_SECRET_KEY` in the environment where you run `scwgw`

See [](./deployment.md) for more information on how to use both approaches to configure your Scaleway CLI.
