#!/usr/bin/env python3
import json

import kong_pdk.pdk.kong as kng  # Avoid clashes with name kong
import requests
from loguru import logger

from gateway.authentication import Auth
from gateway.config import KongConfig
from gateway.log_config import init_logging
from gateway.s3 import Bucket

# Plugin config according to the Kong PDK:
# https://github.com/Kong/kong-python-pdk
PLUGIN_CONF_ADMIN_URL = "admin_url"
Schema = ({PLUGIN_CONF_ADMIN_URL: {"type": "string"}},)
VERSION = "0.1.0"
PRIORITY = 0
PLUGIN_NAME = "scw-sls-auth"


class Plugin(object):
    """
    Main Auth plugin object needed for the Kong PDK
    """

    def __init__(self, config: dict):
        self.admin_url = config.get(PLUGIN_CONF_ADMIN_URL)
        self.kong_conf = KongConfig(self.admin_url)

    @staticmethod
    def _return_kong_response(kong: kng.kong, status: int, body_data: dict):
        kong.response.exit(
            status,
            bytes(json.dumps(body_data), "utf-8"),
            None,
        )

    @staticmethod
    def _return_generated_key(key_url):
        response = requests.get(key_url)
        if response.status_code != requests.codes.ok:
            return response.status_code

        keys_data = response.json()["data"]
        last_generated_key_data = max(keys_data, key=lambda d: d["created_at"])
        return last_generated_key_data["key"]

    @staticmethod
    def _upload_to_bucket(key: str) -> bool:
        client = Bucket()
        return client.upload(key)

    def access(self, kong: kng.kong):
        """
        Called when a user want to generate a key authentication
        """
        method = kong.request.get_method()
        kong.response.set_header("Content-Type", "application/json")

        if method != "POST":
            # Handle unexpected HTTP method
            logger.error(f"Unsupported HTTP method {method}")
            self._return_kong_response(
                kong,
                requests.codes.bad_request,
                {"message": "Unsupported HTTP method"},
            )
            return

        # Generate an API KEY
        auth = Auth()
        auth.from_request()
        err_msg = auth.create(self.kong_conf)

        if err_msg:
            self._return_kong_response(
                kong,
                requests.codes.server_error,
                {"message": f"Request failed: {err_msg}"},
            )
            return

        # Get the generated key
        key_url = f"{self.admin_url}/consumers/{auth.consumer_username}/key-auth"
        result = self._return_generated_key(key_url)

        # Handle unexpected response
        if isinstance(result, int):
            self._return_kong_response(
                kong,
                result,
                {"message": "failed to generate an authentication key"},
            )
            return

        # Upload the key into a s3 bucket
        upload = self._upload_to_bucket(result)
        if not upload:
            self._return_kong_response(
                kong,
                requests.codes.server_error,
                {"message": "failed to generate an authentication key"},
            )
            return

        # Exit successfully
        self._return_kong_response(
            kong,
            requests.codes.ok,
            {"message": "your key has been successfully uploaded to your s3 bucket"},
        )


if __name__ == "__main__":
    init_logging()

    # Start server using Kong PDK
    from kong_pdk.cli import start_dedicated_server

    start_dedicated_server(PLUGIN_NAME, Plugin, VERSION, PRIORITY, Schema)
