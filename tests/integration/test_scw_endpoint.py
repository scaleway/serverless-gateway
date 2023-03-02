import json
import time

from loguru import logger

import requests

GW_HOST = "localhost"
GW_PORT = 8000
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
        "target": "http://ping:80/ping",
        "relative_url": "/ping",
    },
    {
        "http_methods": None,
        "target": "http://ping:80/ping",
        "relative_url": "/scw",
    },
]


class TestEndpoint(object):
    def _call_endpoint_until_response_code(url, code):
        retries = 0
        resp = None
        while retries < 20:
            resp = requests.get(url)
            if resp.status_code == code:
                logger.info(f"Got {resp.status_code} from {url}")
                break

            logger.info(f"Got {resp.status_code} from {url}, retrying")
            time.sleep(3)
            retries += 1

        return resp

    def test_default_list_of_endpoints(self):
        response = requests.get(GW_ADMIN_URL)

        expected_status_code = 200

        actual_endpoints = json.loads(response.content)["endpoints"]
        actual_endpoints_sorted_list = sorted(
            actual_endpoints,
            key=lambda endpoint: (endpoint["relative_url"], endpoint["http_methods"]),
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
        expected_status_code = 200
        expected_func_message = b"Hello from function A"

        request = {
            "target": GW_FUNC_A_URL,
            "relative_url": "/func-a",
        }

        # Create the endpoint and keep calling until it's up
        requests.post(GW_ADMIN_URL, json=request)
        response_gw = self._call_endpoint_until_response_code(
            HOST_GW_FUNC_A_HELLO, expected_status_code
        )
        assert response_gw.status_code == expected_status_code
        assert response_gw.content == expected_func_message

        # Check the endpoint is in the list
        response_endpoints = requests.get(GW_ADMIN_URL)

        expected_endpoints = [
            {
                "http_methods": None,
                "target": "http://func-a:80",
                "relative_url": "/func-a",
            },
            {
                "http_methods": None,
                "target": "http://ping:80/ping",
                "relative_url": "/ping",
            },
            {
                "http_methods": None,
                "target": "http://ping:80/ping",
                "relative_url": "/scw",
            },
        ]

        actual_endpoints = json.loads(response_endpoints.content)["endpoints"]
        actual_endpoints_sorted_list = sorted(
            actual_endpoints,
            key=lambda endpoint: (endpoint["relative_url"], endpoint["http_methods"]),
        )

        assert response_endpoints.status_code == expected_status_code
        assert actual_endpoints_sorted_list == expected_endpoints

        # Now delete the endpoint
        requests.delete(GW_ADMIN_URL, json=request)

        # Keep calling until we get a 404
        response_gw = self._call_endpoint_until_response_code(HOST_GW_FUNC_A_HELLO, 404)

        assert response_gw.status_code == 404
        assert (
            response_gw.content == b'{"message":"no Route matched with those values"}'
        )
