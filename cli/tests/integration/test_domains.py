import time

import requests
from scaleway import ScalewayException

from cli import client
import pytest

from cli.infra import InfraManager
from tests.integration.common import GatewayTest


@pytest.mark.deployed
class TestDomains(GatewayTest):
    def test_adding_domain(self):
        scw_client = client.get_scaleway_client()
        manager = InfraManager(scw_client)

        # Add custom domain using nip.io
        # https://nip.io/
        gw_ip = manager.get_gateway_ip()
        custom_domain = f"{gw_ip}.nip.io"

        # Add domain to the gateway
        # Retry as it will take time to propagate and validate
        success = False
        exception = None
        for retry in range(5):
            time.sleep(10)
            try:
                manager.add_custom_domain(custom_domain)

                success = True
                break
            except ScalewayException as e:
                exception = e

        if not success:
            raise exception

        # Wait for domain to be ready
        manager.await_custom_domain(custom_domain)

        # Add a route
        relative_url = "/cd-test"
        with self.add_route_to_fixture(relative_url):
            # Check call directly
            default_url = f"{self.env.gw_url}{relative_url}/hello"
            resp_default = self.call_endpoint_until_response_code(
                default_url,
                requests.codes.ok,
            )

            full_url = f"https://{custom_domain}{relative_url}/hello"
            resp_domain = self.call_endpoint_until_response_code(
                full_url,
                requests.codes.ok,
            )

            assert resp_default.content == resp_domain.content

        # Remove the domain from the gateway
        manager.delete_custom_domain(custom_domain)
