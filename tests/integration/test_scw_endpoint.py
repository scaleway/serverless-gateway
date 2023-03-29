import json
import time

import boto3
import pytest
import requests
from loguru import logger

GW_HOST = "localhost"
GW_PORT = "8080"

AUTH_URL = f"http://{GW_HOST}:{GW_PORT}/token"
GW_ADMIN_URL = f"http://{GW_HOST}:{GW_PORT}/scw"

FUNC_A_HOST = "localhost"
FUNC_A_PORT = "8004"
FUNC_A_URL = "/func-a"
HOST_FUNC_A_URL = f"http://{FUNC_A_HOST}:{FUNC_A_PORT}"
HOST_FUNC_A_HELLO = f"{HOST_FUNC_A_URL}/hello"
GW_FUNC_A_URL = f"http:/{FUNC_A_URL}"
HOST_GW_FUNC_A_HELLO = f"http://{GW_HOST}:{GW_PORT}{FUNC_A_URL}/hello"

MINIO_BUCKET = "tokens"
MINIO_ENDPOINT = "http://localhost:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
MINIO_REGION = "whatever"


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


@pytest.fixture(scope="module")
def auth_session() -> requests.Session:
    response = requests.post(AUTH_URL)
    assert response.status_code == requests.codes.ok

    s3 = boto3.resource(
        "s3",
        region_name=MINIO_REGION,
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
    )

    # It's important to sort the keys by date because
    # the keys are persisted in the bucket after a container reload
    objects = sorted(
        s3.Bucket(MINIO_BUCKET).objects.all(),
        key=lambda obj: obj.last_modified,
        reverse=True,
    )

    assert objects, "No key was found in bucket!"
    auth_key = objects[0].key

    session = requests.Session()
    session.headers["X-Auth-Token"] = auth_key

    return session


class TestEndpoint(object):
    @staticmethod
    def _call_endpoint_until_response_code(url, code, method: str = "GET"):
        max_retries = 5
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

    def add_route(self, relative_url, auth_session: requests.Session):
        post_request = {
            "target": GW_FUNC_A_URL,
            "relative_url": relative_url,
        }

        auth_session.post(GW_ADMIN_URL, json=post_request)

    def test_default_list_of_endpoints(self, auth_session: requests.Session):
        response = auth_session.get(GW_ADMIN_URL)
        expected_status_code = requests.codes.ok

        assert response.status_code == expected_status_code

        actual_endpoints = json.loads(response.content)["endpoints"]
        actual_endpoints_sorted_list = sorted(
            actual_endpoints,
            key=lambda e: (e["relative_url"]),
        )

        assert actual_endpoints_sorted_list == DEFAULT_ENDPOINTS

    def test_direct_call_to_target(self):
        response = requests.get(HOST_FUNC_A_HELLO)

        expected_status_code = requests.codes.ok
        expected_content = b"Hello from function A"

        assert response.status_code == expected_status_code
        assert response.content == expected_content

    def test_create_delete_endpoint(self, auth_session: requests.Session):
        expected_func_message = b"Hello from function A"

        request = {
            "target": GW_FUNC_A_URL,
            "relative_url": "{FUNC_A_URL}",
        }

        # Create the endpoint and keep calling until it's up
        logger.info(f"Creating new endpoint {request}")
        auth_session.post(GW_ADMIN_URL, json=request)

        response_gw = self._call_endpoint_until_response_code(
            HOST_GW_FUNC_A_HELLO, requests.codes.ok
        )

        assert response_gw.content == expected_func_message

        # Build the expected list of endpoints after adding the new one
        expected_endpoints = [
            {
                "http_methods": [],
                "target": "http://func-a:80",
                "relative_url": "{FUNC_A_URL}",
            },
        ]
        expected_endpoints.extend(DEFAULT_ENDPOINTS)
        expected_endpoints = sorted(
            expected_endpoints,
            key=lambda e: (e["relative_url"]),  # type: ignore
        )

        # Make the request to the SCW plugin
        response_endpoints = auth_session.get(GW_ADMIN_URL)
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
        auth_session.delete(GW_ADMIN_URL, json=request)
        # Keep calling until we get a requests.codes.not_found
        response_gw = self._call_endpoint_until_response_code(
            HOST_GW_FUNC_A_HELLO, requests.codes.not_found
        )

    def test_endpoint_with_http_methods(self, auth_session: requests.Session):
        request = {
            "http_methods": ["PATCH", "PUT"],
            "target": GW_FUNC_A_URL,
            "relative_url": "/func-a",
        }

        try:
            resp = auth_session.post(GW_ADMIN_URL, json=request)
            resp.raise_for_status()

            self._call_endpoint_until_response_code(
                HOST_GW_FUNC_A_HELLO, requests.codes.not_found, "GET"
            )

            self._call_endpoint_until_response_code(
                HOST_GW_FUNC_A_HELLO, requests.codes.ok, "PUT"
            )

            self._call_endpoint_until_response_code(
                HOST_GW_FUNC_A_HELLO, requests.codes.ok, "PATCH"
            )
        finally:
            auth_session.delete(GW_ADMIN_URL, json=request)
            self._call_endpoint_until_response_code(
                HOST_GW_FUNC_A_HELLO, requests.codes.not_found, "PUT"
            )

    def test_cors_enabled_for_target_function(self, auth_session: requests.Session):
        self.add_route(FUNC_A_URL, auth_session)

        cors_headers = {
            "Origin": "https://www.dummy-url.com",
            "Access-Control-Request-Method": "GET",
        }

        response = requests.options(HOST_GW_FUNC_A_HELLO, headers=cors_headers)

        assert response.headers["Access-Control-Allow-Origin"] == "https://www.dummy-url.com"
        assert response.headers["Access-Control-Allow-Headers"] == "*"
        assert (
            response.headers["Access-Control-Allow-Methods"]
            == "GET,HEAD,PUT,PATCH,POST,DELETE,OPTIONS,TRACE,CONNECT"
        )
        assert response.headers["Access-Control-Allow-Credentials"] == "true"
