# Customising your gateway

You can customise the gateway found in this repo.

Once you've made your changes, you can run the following to update your deployment:

```console
scwgw dev update-containers
```

## Observability

The settings for metrics collection can be configured using the following environment variables on your containers:

<!-- markdownlint-disable MD033 -->
| Variable                  | Description                      | Default |
|---------------------------|----------------------------------|---------|
| `METRICS_SCRAPE_INTERVAL` | Time interval to scrape metrics. | 15s     |
| `COCKPIT_METRICS_PUSH_URL` | Cockpit push metrics endpoint. <br/>
Can be found on the Cockpit console page.                           |         |
| `COCKPIT_METRICS_TOKEN`    | Cockpit metrics push token.  <br/> Requires the `write_metrics` scope.                                 |         |
