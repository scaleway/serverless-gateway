from contextlib import contextmanager
from typing import Generator

import click
import requests
import scaleway.cockpit.v1beta1 as sdk
from requests.auth import HTTPBasicAuth
from scaleway import ScalewayException

from cli.console import console

METRICS_TOKEN_NAME = "scw-gw-write-metrics"
WRITE_METRICS_SCOPE = sdk.TokenScopes(
    query_metrics=False,
    write_metrics=True,
    setup_metrics_rules=False,
    query_logs=False,
    write_logs=False,
    setup_logs_rules=False,
    setup_alerts=False,
)

# We create a temporary user to import the dashboard
# This user will be deleted after the import
GRAFANA_TEMPOARY_USER_LOGIN = "tmp-sls-gw-dashboard"
KONG_STATSD_DASHBOARD_ID = "16897"

# TODO: this could be modified by the user
METRICS_DATASOURCE_NAME = "Metrics"


def ensure_cockpit_activated(api: sdk.CockpitV1Beta1API) -> None:
    """Ensure Cockpit is activated"""
    try:
        api.get_cockpit()
        # If successful, cockpit activated
        return
    except ScalewayException as err:
        if not err.status_code == 404:
            raise
        # Activate the cockpit
        click.secho("Activating Cockpit...", fg="yellow")
        cockpit = api.activate_cockpit()
        api.wait_for_cockpit(project_id=cockpit.project_id)
        console.print("Cockpit activated", style="green")


def get_metrics_push_url(api: sdk.CockpitV1Beta1API) -> str:
    """Get the Cockpit metrics push URL."""
    cockpit = api.get_cockpit()

    if not cockpit.endpoints:
        # Should never happen
        raise RuntimeError("Cockpit has no endpoints")

    return cockpit.endpoints.metrics_url + "/api/v1/push"


def get_grafana_url(api: sdk.CockpitV1Beta1API) -> str:
    """Get the Cockpit metrics push URL."""
    cockpit = api.get_cockpit()

    if not cockpit.endpoints:
        # Should never happen
        raise RuntimeError("Cockpit has no endpoints")

    return cockpit.endpoints.grafana_url


def get_metrics_token(api: sdk.CockpitV1Beta1API) -> sdk.Token | None:
    """Get the Cockpit token used to write metrics."""
    tokens = api.list_tokens_all()

    for token in tokens:
        if token.name == METRICS_TOKEN_NAME:
            return token

    return None


def create_metrics_token(api: sdk.CockpitV1Beta1API) -> str:
    """Create a Cockpit token to write metrics."""
    token = api.create_token(
        name=METRICS_TOKEN_NAME,
        scopes=WRITE_METRICS_SCOPE,
    )

    if not token.secret_key:
        # Should never happen
        raise RuntimeError("Token has no secret key")

    return token.secret_key


def delete_metrics_token(api: sdk.CockpitV1Beta1API, token: sdk.Token) -> None:
    """Delete a Cockpit token."""
    api.delete_token(token_id=token.id)


@contextmanager
def temporary_grafana_user(
    api: sdk.CockpitV1Beta1API,
) -> Generator[sdk.GrafanaUser, None, None]:
    """Create a temporary grafana user"""
    user = None
    try:
        user = api.create_grafana_user(
            login=GRAFANA_TEMPOARY_USER_LOGIN, role=sdk.GrafanaUserRole.EDITOR
        )
        yield user
    finally:
        if user:
            api.delete_grafana_user(grafana_user_id=user.id)


def get_metrics_data_source_uid(grafana_url: str, auth: HTTPBasicAuth) -> str:
    """Get the data source uid for the Metrics data source

    This data source is create by Cockpit for external data."""

    resp = requests.get(
        url=grafana_url + f"/api/datasources/name/{METRICS_DATASOURCE_NAME}",
        auth=auth,
        timeout=5,
    )
    resp.raise_for_status()

    return resp.json().get("uid")


def import_kong_statsd_dashboard(
    api: sdk.CockpitV1Beta1API, user: sdk.GrafanaUser
) -> str:
    """Import the Kong StatsD dashboard into Grafana

    Returns the url of the imported dashboard
    """
    url = get_grafana_url(api)

    if not user.password:
        raise RuntimeError(f"provided user {user.login} has no password")
    basic = HTTPBasicAuth(username=user.login, password=user.password)

    # We first get the dashboard from gnet as a json to import it
    resp = requests.get(
        url=url + f"/api/gnet/dashboards/{KONG_STATSD_DASHBOARD_ID}",
        auth=basic,
        timeout=5,
    )
    resp.raise_for_status()

    dashboard_json = resp.json().get("json")
    if not dashboard_json:
        raise RuntimeError("could not find dashboard json")

    # We create the input for the data source
    dashboard_input = {
        "name": "DS_PROMETHEUS",
        "type": "datasource",
        "pluginId": "prometheus",
        "value": get_metrics_data_source_uid(grafana_url=url, auth=basic),
    }

    # We import the dashboard
    resp = requests.post(
        url=url + "/api/dashboards/import",
        auth=basic,
        json={
            "dashboard": dashboard_json,
            "overwrite": True,
            "inputs": [dashboard_input],
        },
        timeout=5,
    )
    resp.raise_for_status()
    data = resp.json()
    return url + data.get("importedUrl")
