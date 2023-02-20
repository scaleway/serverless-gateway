import responses
from kong_pdk.pdk import kong

from gateway.plugin import PLUGIN_CONF_ADMIN_URL, Plugin

DUMMY_ADMIN_URL = "http://foobar"
PLUGIN_CONF = {PLUGIN_CONF_ADMIN_URL: DUMMY_ADMIN_URL}


class DummyKongRequest(object):
    def __init__(self):
        self.method = None

    def get_method(self):
        return self.method

    def set_method(self, method_in):
        self.method = method_in


class TestPlugin(object):
    @responses.activate
    def test_create_endpoint(self):
        kng = kong.kong()

        req = DummyKongRequest()
        req.set_method("GET")
        kng.request = req

        clusters_url = f"{DUMMY_ADMIN_URL}/clusters"
        config_url = f"{DUMMY_ADMIN_URL}/config"

        # Set up request to get config
        config_resp = {
            "config": """
        routes:
          - name: alpha
          - name: beta
        services:
          - name: gamma
          - name: delta
        """
        }

        resp = responses.Response(
            method="GET",
            url=config_url,
            json=config_resp,
        )
        responses.add(resp)

        # Set up request to list clusters
        clusters_resp = {}

        resp = responses.Response(
            method="GET",
            url=clusters_url,
            json=clusters_resp,
        )
        responses.add(resp)

        # Create a plugin instance
        plug = Plugin(PLUGIN_CONF)
        plug.access(kng)
