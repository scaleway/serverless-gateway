import contextlib
import json
import time
from typing import Type

import pytest
import requests
from loguru import logger
from scaleway import Client

from cli import client
from cli.gateway import GatewayManager
from cli.infra import InfraManager
from cli.model import Route
from tests.integration.environment import IntegrationEnvironment


class GatewayTest:
    env: IntegrationEnvironment
    manager: GatewayManager
    infra: InfraManager
    scw_client: Client

    @pytest.fixture(autouse=True, scope="class")
    @classmethod
    def setup(cls: Type["GatewayTest"], integration_env: IntegrationEnvironment):
        cls.env = integration_env
        cls.manager = GatewayManager()
        cls.scw_client = client.get_scaleway_client()
        cls.infra = InfraManager(GatewayTest.scw_client)

    @contextlib.contextmanager
    def add_route_to_fixture(
        self,
        relative_url: str,
        http_methods: list[str] | None = None,
        cors: bool = False,
        jwt: bool = False,
    ):
        """Context manager to add a route and remove it."""
        route = Route(
            relative_url,
            self.env.gw_func_a_url,
            http_methods=http_methods,
            cors=cors,
            jwt=jwt,
        )

        # Make sure it's deleted first
        self.manager.delete_route(route)

        # Now add the route
        resp = self.manager.add_route(route)
        resp.raise_for_status()

        yield relative_url

        resp = self.manager.delete_route(route)
        resp.raise_for_status()

    @staticmethod
    def call_endpoint_until_response_code(url, code, method: str = "GET", headers=None):
        max_retries = 10
        sleep_time = 2

        for _ in range(max_retries):
            resp = requests.request(method=method, url=url, headers=headers)
            if resp.status_code == code:
                logger.info(f"Got {resp.status_code} from {url}")
                return resp

            logger.info(
                f"Got {resp.status_code} from {url}, retrying, message: {resp.text}"
            )
            time.sleep(sleep_time)

        # Here we have failed
        raise RuntimeError(f"Did not get {code} from {url} in {max_retries} tries")

    @staticmethod
    def call_endpoint_until_gw_message(url, message):
        max_retries = 5
        sleep_time = 2

        for _ in range(max_retries):
            resp = requests.get(url)
            if json.loads(resp.content)["message"] == message:
                recieved_message = json.loads(resp.content)["message"]
                logger.info(f"Got {recieved_message} from {url}")
                return resp

            recieved_message = json.loads(resp.content)["message"]
            logger.info(f"Got {recieved_message} from {url}, retrying")
            time.sleep(sleep_time)

        # Here we have failed
        raise RuntimeError(f"Did not get {message} from {url} in {max_retries} tries")
