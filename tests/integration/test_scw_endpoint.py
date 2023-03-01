import time
import json
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


class TestEndpoint(object):
    def test_default_list_of_endpoints(self):

        response = requests.get(GW_ADMIN_URL)

        expected_status_code = 200
        expected_endpoints = [{'http_methods': None, 'target': 'http://ping:80/ping', 'relative_url': '/ping'}, {'http_methods': None, 'target': 'http://ping:80/ping', 'relative_url': '/scw'}]

        actual_endpoints = json.loads(response.content)["endpoints"]
        actual_endpoints_sorted_list = sorted(actual_endpoints, key=lambda endpoint: (endpoint['relative_url'], endpoint['http_methods']))

        assert response.status_code == expected_status_code
        assert actual_endpoints_sorted_list == expected_endpoints

    def test_direct_call_to_target(self):
        
        response = requests.get(HOST_FUNC_A_HELLO)

        expected_status_code = 200
        expected_content = b"Hello from function A"

        assert response.status_code == expected_status_code
        assert response.content == expected_content

    def test_create_endpoint(self):

        request = {
            "target": GW_FUNC_A_URL,
            "relative_url": "/func-a",
        }

        requests.post(GW_ADMIN_URL, json=request)
        # assert response.status_code == 200
        # assert response.content == b'{"message": "Success"}'

        response_endpoints = requests.get(GW_ADMIN_URL)

        expected_status_code = 200
        expected_endpoints = [{"http_methods": None, "target": "http://func-a:80", "relative_url": "/func-a"}, {"http_methods": None, "target": "http://ping:80/ping", "relative_url": "/ping"}, {"http_methods": None, "target": "http://ping:80/ping", "relative_url": "/scw"}]

        actual_endpoints = json.loads(response_endpoints.content)["endpoints"]
        actual_endpoints_sorted_list = sorted(actual_endpoints, key=lambda endpoint: (endpoint['relative_url'], endpoint['http_methods']))

        assert response_endpoints.status_code == expected_status_code
        assert actual_endpoints_sorted_list == expected_endpoints

        retries = 0
        response_gw = None
        while retries < 5:
            response_gw = requests.get(HOST_GW_FUNC_A_HELLO)
            if response_gw.status_code == 200:
                break
            time.sleep(3)
            retries += 1
        
        expected_func_message = b'Hello from function A'

        assert response_gw.status_code == expected_status_code
        assert response_gw.content == expected_func_message

    def test_delete_endpoint(self):
        request = {
            "target": GW_FUNC_A_URL,
            "relative_url": "/func-a",
        }

        requests.post(GW_ADMIN_URL, json=request)

        requests.delete(GW_ADMIN_URL, json=request)
        # assert response.status_code == 200

        # Retry until we get a valid response
        retries = 0
        response_gw = None
        while retries < 5:
            # Invoke relative URL via gateway
            response_gw = requests.get(HOST_GW_FUNC_A_HELLO)
            if response_gw.status_code == 404:
                break

            time.sleep(3)
            retries += 1

        assert response_gw.status_code == 404
        assert (
            response_gw.content == b'{"message":"no Route matched with those values"}'
        )
