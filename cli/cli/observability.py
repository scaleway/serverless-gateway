from scaleway import Client
import scaleway.cockpit.v1beta1 as obs

TOKEN_NAME = "scw-gw-write-metrics"
WRITE_METRICS_SCOPE = obs.TokenScopes(
    query_metrics=False,
    write_metrics=True,
    setup_metrics_rules=False,
    query_logs=False,
    write_logs=False,
    setup_logs_rules=False,
    setup_alerts=False,
)


def get_observability_token(scw_client: Client) -> str:
    """Get the observability token."""
    api = obs.CockpitV1Beta1API(scw_client)
    token = api.create_token(
        name=TOKEN_NAME,
        scopes=WRITE_METRICS_SCOPE,
    )
    if not token.secret_key:
        raise RuntimeError("Token has no secret key")
    return token.secret_key
