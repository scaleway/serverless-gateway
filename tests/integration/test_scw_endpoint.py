import contextlib
import json
import time
import typing

import pytest
import requests
from loguru import logger

from tests.integration.environment import IntegrationEnvironment

DEFAULT_ENDPOINTS = [
    {
        "http_methods": [],
        "target": "http://ping-checker:80/ping",
        "relative_url": "/ping",
    },
    {
        "http_methods": [],
        "target": "http://ping-checker:80/ping",
        "relative_url": "/scw",
    },
    {
        "http_methods": [],
        "target": "http://ping-checker:80/ping",
        "relative_url": "/token",
    },
]


class TestEndpoint(object):
    env: IntegrationEnvironment
    session: requests.Session

    @staticmethod
    @pytest.fixture(autouse=True, scope="class")
    def setup(integration_env: IntegrationEnvironment):
        TestEndpoint.env = integration_env
        TestEndpoint.session = integration_env.get_self.session()

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
        self, relative_url: str, http_methods: list[str] | None = None
    ):
        """Context manager to add a route and remove it."""

        request: dict[str, typing.Any] = {
            "target": self.env.gw_func_a_url,
            "relative_url": relative_url,
        }
        if http_methods:
            request["http_methods"] = http_methods

        resp = self.session.post(self.env.gw_admin_url, json=request)
        resp.raise_for_status()
        yield relative_url
        resp = self.session.delete(self.env.gw_admin_url, json=request)
        resp.raise_for_status()

    def test_default_list_of_endpoints(self):
        response = self.session.get(self.env.gw_admin_url)
        expected_status_code = requests.codes.ok

        assert response.status_code == expected_status_code

        actual_endpoints = json.loads(response.content)["endpoints"]
        actual_endpoints_sorted_list = sorted(
            actual_endpoints,
            key=lambda e: (e["relative_url"]),
        )

        assert actual_endpoints_sorted_list == DEFAULT_ENDPOINTS

    def test_direct_call_to_target(self):
        """Asserts that the upstream function is healthy."""

        response = requests.get(self.env.host_func_a_url + "/hello")

        expected_status_code = requests.codes.ok
        expected_content = b"Hello from function A"

        assert response.status_code == expected_status_code
        assert response.content == expected_content

    def test_create_delete_endpoint(self):
        expected_func_message = b"Hello from function A"

        request = {
            "target": self.env.gw_func_a_url,
            "relative_url": "/func-a",
        }

        # Create the endpoint and keep calling until it's up
        logger.info(f"Creating new endpoint {request}")
        self.session.post(self.env.gw_admin_url, json=request)

        response_gw = self._call_endpoint_until_response_code(
            self.env.gw_url + "/func-a/hello", requests.codes.ok
        )

        assert response_gw.content == expected_func_message

        # Build the expected list of endpoints after adding the new one
        expected_endpoints = [
            {
                "http_methods": [],
                "target": self.env.gw_func_a_url,
                "relative_url": "/func-a",
            },
        ]
        expected_endpoints.extend(DEFAULT_ENDPOINTS)
        expected_endpoints = sorted(
            expected_endpoints,
            key=lambda e: (e["relative_url"]),  # type: ignore
        )

        # Make the request to the SCW plugin
        response_endpoints = self.session.get(self.env.gw_admin_url)
        assert response_endpoints.status_code == requests.codes.ok

        # Parse JSON and check
        actual_endpoints_json = json.loads(response_endpoints.content)
        actual_endpoints = actual_endpoints_json.get("endpoints")

        actual_endpoints_sorted_list = sorted(
            actual_endpoints,
            key=lambda e: (e["relative_url"]),
        )

        assert actual_endpoints_sorted_list == expected_endpoints

        # Now delete the endpoint
        self.session.delete(self.env.gw_admin_url, json=request)
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

    def test_cors_enabled_for_target_function(self):
        with self.add_route_to_fixture(relative_url="/func-a"):
            preflight_req_headers = {
                "Origin": "https://www.dummy-url.com",
                "Access-Control-Request-Method": "GET",
            }

            preflight_resp = requests.options(
                self.env.gw_url + "/func-a/hello", headers=preflight_req_headers
            )

            assert (
                preflight_resp.headers["Access-Control-Allow-Origin"]
                == "https://www.dummy-url.com"
            )
            assert preflight_resp.headers["Access-Control-Allow-Headers"] == "*"
            assert (
                preflight_resp.headers["Access-Control-Allow-Methods"]
                == "GET,HEAD,PUT,PATCH,POST,DELETE,OPTIONS,TRACE,CONNECT"
            )
            assert preflight_resp.headers["Access-Control-Allow-Credentials"] == "true"

    @pytest.mark.parametrize(
            "test_request,expected_status_code,expected_message",
            [
                (
                    {
                        "target": "dummy_url.com",
                        "relative_url": "/dummy",
                    },
                    requests.codes.bad_request,
                    "Invalid request: endpoint target has no http:// or https:// prefix"
                ),
                (
                    {
                        "target": "/dummy_url.com",
                        "relative_url": "/dummy",
                    },
                    requests.codes.bad_request,
                    "Invalid request: endpoint target has no http:// or https:// prefix"
                ),
                (
                    {
                        "target": "http://dummy_url.com",
                        "relative_url": "/dummy",
                    },
                    requests.codes.ok,
                    "Success"
                ),
                (
                    {
                        "target": "https://dummy_url.com",
                        "relative_url": "/dummy",
                    },
                    requests.codes.ok,
                    "Success"
                )
            ]
    )
    def test_prefix_endpoint_validation(self, test_request, expected_status_code, expected_message):
        
        try:
            response = self.session.post(self.env.gw_admin_url, json=test_request)
            assert response.json()["message"] == expected_message
            assert response.status_code == expected_status_code

        finally:
            self.session.delete(self.env.gw_admin_url, json=test_request)
