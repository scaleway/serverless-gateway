# Observability

You can consult metrics for your Kong gateway in Grafana via your [Scaleway Cockpit](https://console.scaleway.com/cockpit/overview).

These metrics include the number of requests per second, the number of errors, the latency, etc.

## Dashboard

You can use the Kong official `statsd` dashboard in your cockpit.

Import it via its id `16897` or by using the following link: <https://grafana.com/grafana/dashboards/16897-kong-statsd-exporter/>.

*Note* you must select the *Metrics* datasource, and not Scaleway Metrics.
