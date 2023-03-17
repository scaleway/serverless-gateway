import json

import kong_pdk.pdk.kong as kng

from gateway.config import KongConfig
from gateway.plugins.plugin_config import PLUGIN_CONF_ADMIN_URL


class ScwPlugin:
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
