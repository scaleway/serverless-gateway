import contextlib
import json
import time

import jwt
import pytest
import requests
from loguru import logger

from cli.gateway import GatewayManager
from cli.model import Consumer, Route
from tests.integration.environment import IntegrationEnvironment


class TestEndpoint(object):
    env: IntegrationEnvironment
    manager: GatewayManager

    @staticmethod
    @pytest.fixture(autouse=True, scope="class")
    def setup(integration_env: IntegrationEnvironment):
        TestEndpoint.env = integration_env
        TestEndpoint.manager = GatewayManager()

    @staticmethod
    def _call_endpoint_until_response_code(url, code, method: str = "GET"):
        max_retries = 10
        sleep_time = 2

        for _ in range(max_retries):
            resp = requests.request(method=method, url=url)
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
    def _call_endpoint_until_gw_message(url, message):
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
        resp = self.manager.add_route(route)
        resp.raise_for_status()

        yield relative_url

        resp = self.manager.delete_route(route)
        resp.raise_for_status()

    def test_direct_call_to_target(self):
        """Asserts that the upstream function is healthy."""
        response = requests.get(self.env.host_func_a_url + "/hello")

        expected_status_code = requests.codes.ok
        expected_content = b"Hello from function A"

        assert response.status_code == expected_status_code
        assert response.content == expected_content

    def test_create_delete_endpoint(self):
        expected_func_message = b"Hello from function A"

        route = Route("/func-a", self.env.gw_func_a_url)
        resp = self.manager.add_route(route)
        resp.raise_for_status()

        response_gw = self._call_endpoint_until_response_code(
            self.env.gw_url + "/func-a/hello", requests.codes.ok
        )

        assert response_gw.content == expected_func_message

        # Build the expected list of endpoints after adding the new one
        expected_routes = [route]

        # Make the request to the SCW plugin
        actual_routes = self.manager.get_routes()
        assert actual_routes == expected_routes

        # Now delete the endpoint
        resp = self.manager.delete_route(route)
        resp.raise_for_status()

        # Keep calling until we get a requests.codes.not_found
        response_gw = self._call_endpoint_until_response_code(
            self.env.gw_url + "/func-a/hello", requests.codes.not_found
        )

    def test_endpoint_with_http_methods(self):
        with self.add_route_to_fixture(
            relative_url="/func-a", http_methods=["PATCH", "PUT"]
        ):
            hello_path = self.env.gw_url + "/func-a/hello"

            # Should not be accessible with GET
            self._call_endpoint_until_response_code(
                hello_path, requests.codes.not_found, "GET"
            )

            self._call_endpoint_until_response_code(
                hello_path, requests.codes.ok, "PUT"
            )

            self._call_endpoint_until_response_code(
                hello_path, requests.codes.ok, "PATCH"
            )

    def test_cors_enabled_for_route(self):
        with self.add_route_to_fixture(relative_url="/func-a", cors=True):
            # Leave time for plugin to be installed
            time.sleep(10)
            preflight_req_headers = {
                "Origin": "https://www.dummy-url.com",
                "Access-Control-Request-Method": "GET",
            }

            preflight_resp = requests.options(
                self.env.gw_url + "/func-a/hello", headers=preflight_req_headers
            )

            assert (
                preflight_resp.headers.get("Access-Control-Allow-Origin")
                == "https://www.dummy-url.com"
            )

            assert preflight_resp.headers.get("Access-Control-Allow-Headers") == "*"

            assert (
                preflight_resp.headers.get("Access-Control-Allow-Methods")
                == "GET,HEAD,PUT,PATCH,POST,DELETE,OPTIONS,TRACE,CONNECT"
            )
            assert preflight_resp.headers["Access-Control-Allow-Credentials"] == "true"

    def test_add_remove_consumers(self):
        consumer_name_a = "alpha"
        consumer_name_b = "beta"

        # Make sure we've cleaned up
        self.manager.delete_consumer(consumer_name_a)
        self.manager.delete_consumer(consumer_name_b)

        # Check list empty initially
        consumers = self.manager.get_consumers()
        assert len(consumers) == 0

        # Add two consumers
        self.manager.add_consumer(consumer_name_a)
        self.manager.add_consumer(consumer_name_b)

        # Get list and check
        consumers = self.manager.get_consumers()
        consumers.sort(key=lambda x: x.username)

        expected = [
            Consumer(consumer_name_a),
            Consumer(consumer_name_b),
        ]
        assert consumers == expected

        # Delete one, check list again
        self.manager.delete_consumer(consumer_name_a)
        consumers = self.manager.get_consumers()
        expected = [
            Consumer(consumer_name_b),
        ]
        assert consumers == expected

    def test_jwt_requires_auth(self):
        consumer_name = "test-app"
        self.manager.delete_consumer(consumer_name)

        relative_url = "/auth-test"
        full_url = f"{self.env.gw_url}/{relative_url}/hello"
        with self.add_route_to_fixture(relative_url=relative_url, jwt=True):
            # Leave time for plugin to be installed
            time.sleep(10)

            # Unauthed request should fail
            no_auth_resp = requests.get(full_url)
            assert no_auth_resp.status_code == requests.codes.unauthorized

            # Request with invalid auth should fail
            bad_auth_resp = requests.get(
                full_url,
                headers={
                    "Authorization": "Bearer foobar",
                },
            )
            assert bad_auth_resp.status_code == requests.codes.unauthorized

            # Generate a valid token
            self.manager.add_consumer(consumer_name)
            cred = self.manager.add_jwt_cred(consumer_name)

            encoded = jwt.encode(
                {"foo": "bar", "iss": cred.iss}, cred.secret, algorithm=cred.algorithm
            )

            # Request with valid auth should pass
            good_auth_headers = {
                "Authorization": f"Bearer {encoded}",
            }
            good_auth_resp = requests.get(
                full_url,
                headers=good_auth_headers,
            )
            assert good_auth_resp.status_code == requests.codes.ok

    @pytest.mark.parametrize(
        "target",
        [
            ("dummy_url.com",),
            ("/dummy_url.com",),
        ],
    )
    def test_invalid_url_formats(self, target):
        route = Route("/foo", target)

        with pytest.raises(requests.HTTPError):
            self.manager.add_route(route)

    @pytest.mark.parametrize(
        "target,expected",
        [
            (
                "http://dummy_url.com",
                "http://dummy_url.com:80",
            ),
            (
                "https://dummy_url.com",
                "https://dummy_url.com:443",
            ),
            (
                "https://foobar.com:8005",
                "https://foobar.com:8005",
            ),
        ],
    )
    def test_valid_url_formats(self, target, expected):
        route = Route("/foo", target)

        resp = self.manager.add_route(route)
        assert resp.status_code == requests.codes.ok

        # Get route
        routes = self.manager.get_routes()
        matches = [r for r in routes if r.relative_url == "/foo"]

        assert len(matches) == 1
        actual_route = matches[0]

        assert actual_route.target == expected

        self.manager.delete_route(route)
