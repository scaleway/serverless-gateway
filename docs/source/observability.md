# Observability

You can consult metrics for your Kong gateway in Grafana via your [Scaleway Cockpit](https://console.scaleway.com/cockpit/overview).

These metrics include the number of requests per second, the number of errors, the latency, etc.

## Dashboard

The deployment tool will automatically import a Grafana dashboard for Kong. This dashboard gives you a quick overview of the health of your Kong gateway.

The url of the dashboard will be displayed at the end of the deployment.

Initially, the dashboard will be empty. You will need to add some routes to your Kong gateway to start seeing metrics.
