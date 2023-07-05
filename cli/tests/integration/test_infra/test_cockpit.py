import uuid
from typing import Generator

import pytest
import requests
from requests.auth import HTTPBasicAuth
from scaleway import Client, ScalewayException
from scaleway.account import v2 as account
from scaleway.cockpit import v1beta1 as sdk

import cli.infra.cockpit as cpt


@pytest.fixture(scope="module")
def api() -> Generator[sdk.CockpitV1Beta1API, None, None]:
    """Return a Cockpit API on a temporary project."""
    client = Client.from_config_file_and_env()
    api = account.AccountV2API(client)
    project = None
    try:
        project = api.create_project(
            name=f"test-cockpit-{uuid.uuid4()}",
            description="Generated by gateway integration tests",
        )
        client.default_project_id = project.id
        yield sdk.CockpitV1Beta1API(client)
    finally:
        if project:
            # We need to delete cockpit if it was created
            cockpit_api = sdk.CockpitV1Beta1API(client)
            cockpit_api.deactivate_cockpit(project_id=project.id)
            try:
                cockpit_api.wait_for_cockpit(project_id=project.id)
            except ScalewayException as err:
                if not err.status_code == 404:
                    raise
            api.delete_project(project_id=project.id)


def test_ensure_cockpit_activated(api: sdk.CockpitV1Beta1API):
    cpt.ensure_cockpit_activated(api=api)

    cockpit = api.get_cockpit()
    assert cockpit is not None


def test_get_metrics_push_url(api: sdk.CockpitV1Beta1API):
    cpt.ensure_cockpit_activated(api=api)

    url = cpt.get_metrics_push_url(api=api)
    assert url is not None
    assert url.startswith("https://metrics.")
    assert url.endswith("/api/v1/push")


def test_temporary_grafana_user(api: sdk.CockpitV1Beta1API):
    with cpt.temporary_grafana_user(api=api) as user:
        assert user is not None
        assert user.login == "tmp-sls-gw-dashboard"
        assert user.password is not None
        assert len(user.password) == 16

    # Assert that the user has been deleted
    users = api.list_grafana_users_all()
    assert not any(user.login == "tmp-sls-gw-dashboard" for user in users)


def test_get_metrics_data_source_uid(api: sdk.CockpitV1Beta1API):
    with cpt.temporary_grafana_user(api=api) as user:
        url = cpt.get_grafana_url(api=api)
        assert user.password is not None
        basic = HTTPBasicAuth(user.login, user.password)

        uid = cpt.get_metrics_data_source_uid(grafana_url=url, auth=basic)
        assert len(uid) == 17
        assert uid.isalnum()
        # Schema: PA<15 alphanumeric characters>
        assert uid.startswith("PA")


def test_import_kong_statsd_dashboard(api: sdk.CockpitV1Beta1API):
    with cpt.temporary_grafana_user(api=api) as user:
        url = cpt.import_kong_statsd_dashboard(api=api, user=user)
        assert url is not None
        assert url.endswith("kong-statsd-exporter-offcial")

        # Assert that the page is accessible
        assert user.password is not None
        basic = HTTPBasicAuth(user.login, user.password)
        response = requests.get(url, auth=basic, timeout=5)
        assert response.status_code == 200

        # Get the dashboard uid from its url
        uid = url.split("/")[-2]

        # Use the API to get the dashboard
        grafana_url = cpt.get_grafana_url(api=api)
        resp = requests.get(
            url=grafana_url + f"/api/dashboards/uid/{uid}",
            auth=basic,
            timeout=5,
        )
        assert resp.status_code == 200
        resp_json = resp.json()

        # Assert that the dashboard is the one we expect
        assert resp_json["dashboard"]["title"] == "Kong statsd exporter(offcial)"
