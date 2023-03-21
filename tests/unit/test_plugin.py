import responses
from kong_pdk.pdk import kong

from gateway.plugins.plugin_config import PLUGIN_CONF_ADMIN_URL
from gateway.plugins.scw import Plugin

DUMMY_ADMIN_URL = "http://dummy-admin-url"
PLUGIN_CONF = {PLUGIN_CONF_ADMIN_URL: DUMMY_ADMIN_URL}


class DummyKongRequest(object):
    def __init__(self):
        self.method = None

    def get_method(self):
        return self.method

    def set_method(self, method_in):
        self.method = method_in

    def get_body(self):
        return self.body

    def set_body(self, newBody):
        self.body = newBody


class TestPlugin(object):
    @responses.activate
    def test_get_config(self):
        kongGW = kong.kong()
        dummyRequest = DummyKongRequest()
        dummyRequest.set_method("GET")

        kongGW.request = dummyRequest

        config_url = f"{DUMMY_ADMIN_URL}/config"

        config_resp = {
            "config": """
        routes:
          - name: route_1
          - name: route_2
        services:
          - name: service_1
          - name: service_2
        """
        }

        resp = responses.Response(
            method="GET",
            url=config_url,
            json=config_resp,
        )
        responses.add(resp)

        # Create a plugin instance
        plug = Plugin(PLUGIN_CONF)
        plug.access(kongGW)

    @responses.activate
    def test_add_config(self):
        kongGW = kong.kong()
        dummyRequest = DummyKongRequest()
        dummyRequest.set_method("POST")
        body = {"http_method": "POST", "relative_url": "/test"}
        dummyRequest.set_body(body)
        kongGW.request = dummyRequest

        config_url = f"{DUMMY_ADMIN_URL}/config"

        config_resp = {
            "config": """
        routes:
          - name: route_1
          - name: route_2
        services:
          - name: service_1
          - name: service_2
        """
        }

        newConfig = {"_format_version": "3.0"}

        getConfigResponse = responses.Response(
            method="GET",
            url=config_url,
            json=config_resp,
        )
        responses.add(getConfigResponse)

        postConfigResponse = responses.Response(
            method="POST", url=config_url, json=newConfig
        )
        responses.add(postConfigResponse)

        # Create a plugin instance
        plug = Plugin(PLUGIN_CONF)
        plug.access(kongGW)
