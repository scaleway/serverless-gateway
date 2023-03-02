#!/usr/bin/env python3
import json

import kong_pdk.pdk.kong as kng
import requests
from loguru import logger

from .config import KongConfig
from .endpoint import Endpoint
from .log_config import init_logging

# Plugin config according to the Kong PDK:
# https://github.com/Kong/kong-python-pdk
PLUGIN_CONF_ADMIN_URL = "admin_url"
Schema = ({PLUGIN_CONF_ADMIN_URL: {"type": "string"}},)
VERSION = "0.1.0"
PRIORITY = 0
PLUGIN_NAME = "scw-sls-gw"


class Plugin(object):
    """
    Main plugin object needed for the Kong PDK
    """

    def __init__(self, config):
        self.admin_url = config.get(PLUGIN_CONF_ADMIN_URL)
        self.kong_conf = KongConfig(self.admin_url)

    def _return_kong_response(self, kong: kng.kong, status: int, body_data: dict):
        kong.response.exit(
            status,
            bytes(json.dumps(body_data), "utf-8"),
            None,
        )

    def access(self, kong: kng.kong):
        """
        Called whenever an endpoint bound to this plugin is accessed
        """
        method = kong.request.get_method()

        kong.response.set_header("Content-Type", "application/json")

        # Take action based on the HTTP method
        if method == "GET":
            # Return list of configured endpoints
            endpoints = self.kong_conf.get_endpoints()
            self._return_kong_response(kong, requests.codes.ok, endpoints)
            return

        elif method in ("POST", "DELETE"):
            # Extract body from request
            body_data = kong.request.get_body()
            logger.info(f"SCW plugin got payload: {body_data}")

            # Construct and validate an endpoint
            endpoint = Endpoint.from_json(body_data)
            err_msg = endpoint.validate()
            if err_msg:
                self._return_kong_response(
                    kong,
                    requests.codes.bad_request,
                    {"message": f"Invalid request: {err_msg}"},
                )
                return

            # Delete or create endpoint depending on HTTP method
            if method == "DELETE":
                err_msg = endpoint.delete(self.kong_conf)
            else:
                err_msg = endpoint.create(self.kong_conf)

            if err_msg:
                self._return_kong_response(
                    kong,
                    requests.codes.server_error,
                    {"message": f"Request failed: {err_msg}"},
                )
                return

        else:
            # Handle unexpected HTTP method
            logger.error(f"Unsupported HTTP method {method}")
            self._return_kong_response(
                kong,
                requests.codes.bad_request,
                {"message": "Unsupported HTTP method"},
            )
            return

        # Exit successfully
        self._return_kong_response(
            kong,
            requests.codes.ok,
            {"message": "Success"},
        )


if __name__ == "__main__":
    init_logging()

    # Start server using Kong PDK
    from kong_pdk.cli import start_dedicated_server

    start_dedicated_server(PLUGIN_NAME, Plugin, VERSION, PRIORITY, Schema)
