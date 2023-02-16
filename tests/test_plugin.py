import time

import requests

GW_HOST = "localhost"
GW_PORT = 8000
GW_ADMIN_URL = f"http://{GW_HOST}:{GW_PORT}/scw"

HOST_FUNC_A_URL = "http://localhost:8004"
HOST_FUNC_A_HELLO = f"{HOST_FUNC_A_URL}/hello"

GW_FUNC_A_URL = "http://func-a"

HOST_GW_FUNC_A_HELLO = f"http://{GW_HOST}:{GW_PORT}/func-a/hello"


class TestPlugin(object):
    def test_create_endpoint(self):
        # Call target directly
        print("Calling func A direct")
        resp_direct = requests.get(HOST_FUNC_A_HELLO)
        assert resp_direct.status_code == 200
        assert resp_direct.content == b"Hello from function A"

        print("Requesting func A creation")
        req = {
            "target": GW_FUNC_A_URL,
            "relative_url": "/func-a",
        }
        resp = requests.post(GW_ADMIN_URL, json=req)
        assert resp.status_code == 200

        # Retry until we get a valid response
        retries = 0
        resp_gw = None
        while retries < 5:
            # Invoke relative URL via gateway
            resp_gw = requests.get(HOST_GW_FUNC_A_HELLO)
            if resp_gw.status_code == 200:
                break

            time.sleep(3)
            retries += 1

        assert resp_gw.status_code == 200
        assert resp_gw.content == b"Hello from function A"
