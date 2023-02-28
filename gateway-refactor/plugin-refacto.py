#!/usr/bin/env python3
import json

import kong_pdk.pdk.kong as kong
import requests
from loguru import logger

from .config import KongConfig
from .endpoint import Endpoint

# Plugin config according to the Kong PDK:
# https://github.com/Kong/kong-python-pdk
PLUGIN_CONF_ADMIN_URL = "admin_url"
Schema = ({PLUGIN_CONF_ADMIN_URL: {"type": "string"}},)
VERSION = "0.1.0"
PRIORITY = 0
PLUGIN_NAME = "scw-sls-gw"


# Main plugin object needed for the Kong PDK
class Plugin(object):
    def __init__(self, config):
        self.admin_url = config.get(PLUGIN_CONF_ADMIN_URL)
        self.kong_conf = KongConfig(self.admin_url)

    def access(self, kong: kong.kong):
        """
        Called whenever an endpoint bound to this plugin is accessed
        """
        method = kong.request.get_method()

        kong.response.set_header("Content-Type", "application/json")

        # Take action based on the HTTP method
        if method == "GET":
            # Return list of configured endpoints
            endpoints = self.kong_conf.get_endpoints()
            kong.response.exit(
                requests.codes.ok, bytes(json.dumps(endpoints), "utf-8"), None
            )
            return

        elif method in ("POST", "DELETE"):
            # Extract body from request
            body_data = kong.request.get_body()
            logger.info(f"SCW plugin got payload: {body_data}")

            # Construct and validate an endpoint
            endpoint = Endpoint.from_json(body_data)
            err_msg = endpoint.validate()
            if err_msg:
                kong.response.exit(
                    status=requests.codes.bad_request,
                    body=bytes(
                        json.dumps({"message": f"Invalid request: {err_msg}"}), "utf-8"
                    ),
                    headers=None,
                )
                return

            # Delete or create endpoint depending on HTTP method
            if method == "DELETE":
                err_msg = endpoint.delete(self.kong_conf)
            else:
                err_msg = endpoint.create(self.kong_conf)

            if err_msg:
                kong.response.exit(
                    status=requests.codes.server_error,
                    body=bytes(
                        json.dumps({"message": f"Request failed: {err_msg}"}), "utf-8"
                    ),
                    headers=None,
                )
                return

        else:
            # Handle unexpected HTTP method
            logger.error(f"Unsupported HTTP method {method}")
            kong.response.exit(
                status=requests.codes.bad_request,
                body=bytes(json.dumps({"message": "Unsupported HTTP method"}), "utf-8"),
                headers=None,
            )
            return

        # Exit successfully
        kong.response.exit(
            status=requests.codes.ok,
            body=bytes(json.dumps({"message": "Success"}), "utf-8"),
            headers=None,
        )


if __name__ == "__main__":
    # Start server using Kong PDK
    from kong_pdk.cli import start_dedicated_server

    start_dedicated_server(PLUGIN_NAME, Plugin, VERSION, PRIORITY, Schema)
