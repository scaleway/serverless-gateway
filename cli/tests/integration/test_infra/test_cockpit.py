from typing import Type
import pytest
import requests
from requests.auth import HTTPBasicAuth
from scaleway import Client, ScalewayException
from scaleway.account import v2 as account
from scaleway.cockpit import v1beta1 as sdk

import cli.infra.cockpit as cpt


@pytest.mark.deployed
class TestCockpit:
    """Test suite for cockpit integration."""

    @pytest.fixture(autouse=True, scope="class")
    @classmethod
    def setup(cls: Type["TestCockpit"], tmp_scaleway_project: account.Project):
        client = Client.from_config_file_and_env()
        client.default_project_id = tmp_scaleway_project.id
        cls.api = sdk.CockpitV1Beta1API(client)
        cpt.ensure_cockpit_activated(api=cls.api)

        # Create an API on the default_project
        client = Client.from_config_file_and_env()
        cls.default_project_api = sdk.CockpitV1Beta1API(client)
        cpt.ensure_cockpit_activated(api=cls.default_project_api)

    @classmethod
    def teardown_class(cls: Type["TestCockpit"]):
        # Deactivate cockpit on the temporary project
        cls.api.deactivate_cockpit()
        try:
            cls.api.wait_for_cockpit()
        except ScalewayException as err:
            if not err.status_code == 404:
                raise

    def test_ensure_cockpit_activated(self):
        cockpit = self.api.get_cockpit()
        assert cockpit is not None
        assert cockpit.status == sdk.CockpitStatus.READY

    def test_get_metrics_push_url(self):
        url = cpt.get_metrics_push_url(api=self.api)
        assert url is not None
        assert url.startswith("https://metrics.")
        assert url.endswith("/api/v1/push")

    # For some reason, running the next test against a recently created cockpit
    # fails with a 500 error. Because a user is necessary for the next few tests,
    # run them against the default project cockpit instead.
    # TODO: investigate
    def test_temporary_grafana_user(self):
        api = self.default_project_api

        with cpt.temporary_grafana_user(api=api) as user:
            assert user is not None
            assert user.login == "tmp-sls-gw-dashboard"
            assert user.password is not None
            assert len(user.password) == 16

        # Assert that the user has been deleted
        users = api.list_grafana_users_all()
        assert not any(user.login == "tmp-sls-gw-dashboard" for user in users)

    def test_get_metrics_data_source_uid(self):
        api = self.default_project_api

        with cpt.temporary_grafana_user(api=api) as user:
            url = cpt.get_grafana_url(api=api)
            assert user.password is not None
            basic = HTTPBasicAuth(user.login, user.password)

            uid = cpt.get_metrics_data_source_uid(grafana_url=url, auth=basic)
            assert len(uid) == 17
            assert uid.isalnum()
            # Schema: PA<15 alphanumeric characters>
            assert uid.startswith("PA")

    def test_import_kong_statsd_dashboard(self):
        api = self.default_project_api

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
