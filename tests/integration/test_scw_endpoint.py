import json
import time

import requests
from loguru import logger

GW_HOST = "localhost"
GW_PORT = "8000"
GW_ADMIN_URL = f"http://{GW_HOST}:{GW_PORT}/scw"

FUNC_A_HOST = "localhost"
FUNC_A_PORT = "8004"
HOST_FUNC_A_URL = f"http://{FUNC_A_HOST}:{FUNC_A_PORT}"
HOST_FUNC_A_HELLO = f"{HOST_FUNC_A_URL}/hello"
GW_FUNC_A_URL = "http://func-a"
HOST_GW_FUNC_A_HELLO = f"http://{GW_HOST}:{GW_PORT}/func-a/hello"


DEFAULT_ENDPOINTS = [
    {
        "http_methods": None,
        "target": "http://ping-checker:80/ping",
        "relative_url": "/ping",
    },
    {
        "http_methods": None,
        "target": "http://ping-checker:80/ping",
        "relative_url": "/scw",
    },
]


class TestEndpoint(object):
    def _call_endpoint_until_response_code(self, url, code):
        max_retries = 20
        sleep_time = 3
        resp = None

        for r in range(max_retries):
            resp = requests.get(url)
            if resp.status_code == code:
                logger.info(f"Got {resp.status_code} from {url}")
                return resp

            logger.info(f"Got {resp.status_code} from {url}, retrying")
            time.sleep(sleep_time)

        # Here we have failed
        raise RuntimeError(f"Did not get {code} from {url} in {max_retries} tries")

    def test_default_list_of_endpoints(self):
        response = requests.get(GW_ADMIN_URL)

        expected_status_code = 200

        actual_endpoints = json.loads(response.content)["endpoints"]
        actual_endpoints_sorted_list = sorted(
            actual_endpoints,
            key=lambda e: (e["relative_url"]),
        )

        assert response.status_code == expected_status_code
        assert actual_endpoints_sorted_list == DEFAULT_ENDPOINTS

    def test_direct_call_to_target(self):
        response = requests.get(HOST_FUNC_A_HELLO)

        expected_status_code = 200
        expected_content = b"Hello from function A"

        assert response.status_code == expected_status_code
        assert response.content == expected_content

    def test_create_delete_endpoint(self):
        expected_func_message = b"Hello from function A"

        request = {
            "target": GW_FUNC_A_URL,
            "relative_url": "/func-a",
        }

        # Create the endpoint and keep calling until it's up
        logger.info(f"Creating new endpoint {request}")
        requests.post(GW_ADMIN_URL, json=request)

        response_gw = self._call_endpoint_until_response_code(HOST_GW_FUNC_A_HELLO, 200)

        assert response_gw.content == expected_func_message

        # Build the expected list of endpoints after adding the new one
        expected_endpoints = [
            {
                "http_methods": None,
                "target": "http://func-a:80",
                "relative_url": "/func-a",
            },
            {
                "http_methods": None,
                "target": "http://ping-checker:80/ping",
                "relative_url": "/ping",
            },
            {
                "http_methods": None,
                "target": "http://ping-checker:80/ping",
                "relative_url": "/scw",
            },
        ]

        # Make the request to the SCW plugin
        response_endpoints = requests.get(GW_ADMIN_URL)
        assert response_endpoints.status_code == 200

        # Parse JSON and check
        actual_endpoints_json = json.loads(response_endpoints.content)
        actual_endpoints = actual_endpoints_json.get("endpoints")

        actual_endpoints_sorted_list = sorted(
            actual_endpoints,
            key=lambda e: (e["relative_url"]),
        )

        assert actual_endpoints_sorted_list == expected_endpoints

        # Now delete the endpoint
        requests.delete(GW_ADMIN_URL, json=request)

        # Keep calling until we get a 404
        response_gw = self._call_endpoint_until_response_code(HOST_GW_FUNC_A_HELLO, 404)
        assert (
            response_gw.content == b'{"message":"no Route matched with those values"}'
        )
