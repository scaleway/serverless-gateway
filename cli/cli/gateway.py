import requests
from loguru import logger
from scaleway import Client
from scaleway.container.v1beta1 import ContainerV1Beta1API

from cli.model import Route


class GatewayManager(object):
    def __init__(
        self,
        admin_url,
        local=False,
    ):
        self.admin_url = admin_url
        self.routes_url = admin_url + "/routes"
        self.services_url = admin_url + "/services"

        if local:
            self.auth_headers = {}
            self.scw_client = None
            self.containers = None
        else:
            # TODO - add auth for deployed container
            self.auth_headers = {} if local else {}

            # Initialise SCW client
            self.scw_client = Client.from_config_file_and_env(profile_name="dev")

            # Initi Scaleway APIs
            self.containers = ContainerV1Beta1API(self.scw_client)

    def _get_gateway_container(
        self,
    ):
        # TODO - use API to get deployed gateway container
        pass

    def add_route(self, route: Route):
        service_url = f"{self.services_url}/{route.name}"
        route_url = f"{self.routes_url}/{route.name}"

        self._do_request("PUT", service_url, data=route.service_json())
        resp = self._do_request("PUT", route_url, data=route.route_json())

        if route.cors:
            plugins_url = f"{route_url}/plugins"

            try:
                self._do_request("POST", plugins_url, data=route.cors_json())
            except requests.HTTPError:
                # TODO - avoid ignoring this, any way to create or update?
                pass

        return resp

    def delete_route(self, route: Route):
        self._do_request("DELETE", f"{self.routes_url}/{route.name}")
        resp = self._do_request("DELETE", f"{self.services_url}/{route.name}")
        return resp

    def get_routes(self):
        resp = self._do_request("GET", self.routes_url)
        route_data = {r.get("name"): r for r in resp.json().get("data")}

        resp = self._do_request("GET", self.services_url)
        service_data = {s.get("name"): s for s in resp.json().get("data")}

        routes = list()
        for _, r in route_data.items():
            name = r["name"]
            relative_url = r["paths"][0]
            http_methods = r.get("methods")

            s = service_data.get(name)
            port = s["port"]
            host = s["host"]
            protocol = s["protocol"]
            url = f"{protocol}://{host}:{port}"

            routes.append(Route(relative_url, url, http_methods=http_methods))

        return routes

    def _do_request(self, method, url, data=None) -> requests.Response:
        logger.debug(f"{method}: {url}")

        if method == "GET":
            resp = requests.get(url, headers=self.auth_headers)
        elif method == "DELETE":
            resp = requests.delete(url, headers=self.auth_headers)
        elif method == "PATCH":
            resp = requests.patch(url, headers=self.auth_headers, json=data)
        elif method == "POST":
            resp = requests.post(url, headers=self.auth_headers, json=data)
        elif method == "PUT":
            resp = requests.put(url, headers=self.auth_headers, json=data)
        else:
            logger.error(f"Invalid method: {method}")
            raise RuntimeError("Invalid HTTP method")

        resp.raise_for_status()

        return resp
