# Observability

## Cockpit

With Cockpit, you can consult the metrics of your Kong gateway in a Grafana instance. For instance, you can consult the number of requests per second, the number of errors, the latency, etc.

By default, the Cockpit integration is enabled when you create the containers, but you may disable it by passing `no-metrics` to the `scwgw` CLI helper.

```console
scwgw create-containers --no-metrics
```

## Configuring

<!-- markdownlint-disable MD033 -->
| Variable                  | Description                      | Default |
|---------------------------|----------------------------------|---------|
| `METRICS_SCRAPE_INTERVAL` | Time interval to scrape metrics. | 15s     |
| `COCKPIT_METRICS_PUSH_URL` | Cockpit push metrics endpoint. <br/>
Can be found on the Cockpit console page.                           |         |
| `COCKPIT_METRICS_TOKEN`    | Cockpit metrics push token.  <br/> Requires the `write_metrics` scope.                                 |         |

## Running

To export the metrics, the `statsd` plugin must be enabled on the Kong gateway. You can enable it globally via a CLI helper:

```console
# This will install the statsd Kong plugin
scwgw setup-metrics
```

Finally, you can use the Kong official statsd plugin to consult your metrics in Cockpit's Grafana instance. You can import the dashboard via its id `16897` or by using the following link: <https://grafana.com/grafana/dashboards/16897-kong-statsd-exporter/>.
