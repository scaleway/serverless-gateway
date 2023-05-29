import click
from scaleway import Client, ScalewayException
import scaleway.cockpit.v1beta1 as sdk

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


def ensure_cockpit_activated(scw_client: Client) -> bool:
    """Ensure Cockpit is activated.

    Prompt the user to activate cockpit if it is not activated.
    """
    api = sdk.CockpitV1Beta1API(scw_client)
    try:
        api.get_cockpit()
        return True
    except ScalewayException as err:
        if not err.status_code == 404:
            raise

        project_id = scw_client.default_project_id
        should_activate_cockpit = click.confirm(
            f"Cockpit is not activated for project {project_id}. Do you want to activate it?",
        )

        if not should_activate_cockpit:
            return False
        cockpit = api.activate_cockpit()
        api.wait_for_cockpit(project_id=cockpit.project_id)
        click.secho("Cockpit activated", fg="green")

        return True


def get_metrics_push_url(api: sdk.CockpitV1Beta1API) -> str:
    """Get the Cockpit metrics push URL."""
    cockpit = api.get_cockpit()

    if not cockpit.endpoints:
        # Should never happen
        raise RuntimeError("Cockpit has no endpoints")

    return cockpit.endpoints.metrics_url + "/api/v1/push"


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


def delete_metrics_token_by_name(api: sdk.CockpitV1Beta1API) -> None:
    """Delete a Cockpit token by its name."""
    tokens = api.list_tokens_all()
    for token in tokens:
        if token.name == METRICS_TOKEN_NAME:
            delete_metrics_token(token)


def delete_metrics_token(api: sdk.CockpitV1Beta1API, token: sdk.Token) -> None:
    """Delete a Cockpit token."""
    api.delete_token(token_id=token.id)