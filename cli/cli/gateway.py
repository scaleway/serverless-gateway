import typing as t
from collections import defaultdict
from dataclasses import dataclass

import requests
from loguru import logger
from requests import Response
from requests.adapters import HTTPAdapter
from rich.table import Table
from urllib3 import Retry

from cli import conf
from cli.console import console
from cli.model import Consumer, JwtCredential, Route

MAX_RETRIES = 5


@dataclass
class KongAPIException(Exception):
    """Exception raised when the Kong API returns an error."""

    response: Response

    def __str__(self) -> str:
        """Return the response text."""
        return self.response.text


class GatewayManager:
    """Configure routes via the Kong admin API."""

    admin_url: str
    gateway_url: str

    def __init__(self, config: t.Optional[conf.InfraConfiguration] = None):
        # Local local config
        self.config = config or conf.InfraConfiguration.load()
        self.admin_url = self.config.gw_admin_url
        self.gateway_url = self.config.gw_url

        self.routes_url = self.admin_url + "/routes"
        self.services_url = self.admin_url + "/services"
        self.consumers_url = self.admin_url + "/consumers"
        self.plugins_url = self.admin_url + "/plugins"

        self.token = self.config.gw_admin_token

        self._session = self._get_session()

    def _get_session(self) -> requests.Session:
        session = requests.Session()
        if self.token:
            session.headers["X-Auth-Token"] = self.token

        retries = Retry(
            total=MAX_RETRIES,
            backoff_factor=2,
            status=MAX_RETRIES,  # Status max retries
            # 403: retry for token refresh
            # 404: retry for Envoy service not found
            status_forcelist=[500, 404, 403],
        )
        session.mount("https://", HTTPAdapter(max_retries=retries))

        return session

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make a request to the Kong admin API."""
        try:
            logger.debug(f"Request: {method} {url}")
            resp = self._session.request(method, url, **kwargs)
            logger.debug(f"Response: {resp.status_code} {resp.text}")
            resp.raise_for_status()
            return resp
        except requests.HTTPError as err:
            raise KongAPIException(err.response) from err

    def add_route(self, route: Route) -> requests.Response:
        """Add a route to Kong."""

        if not route.target.startswith("http"):
            raise ValueError("Route target must start with http or https")

        service_url = f"{self.services_url}/{route.name}"
        route_url = f"{self.routes_url}/{route.name}"

        resp = self._request(method="PUT", url=service_url, json=route.service_json())
        resp = self._request(method="PUT", url=route_url, json=route.route_json())

        route_plugins_url = f"{route_url}/plugins"

        if route.cors:
            try:
                self._request(
                    method="POST", url=route_plugins_url, json=route.cors_json()
                )
            except KongAPIException as err:
                # Ignore if the plugin already exists
                if err.response.status_code != 409:
                    raise

        if route.jwt:
            try:
                self._request(
                    method="POST", url=route_plugins_url, json=route.jwt_json()
                )
            except KongAPIException as err:
                # Ignore if the plugin already exists
                if err.response.status_code != 409:
                    raise

        return resp

    def delete_route(self, route: Route) -> requests.Response:
        """Delete a route from Kong."""
        self._request(method="DELETE", url=f"{self.routes_url}/{route.name}")
        resp = self._request(method="DELETE", url=f"{self.services_url}/{route.name}")
        return resp

    def print_routes(self) -> None:
        """Print all routes."""
        routes: list[Route] = self.get_routes()
        routes.sort(key=lambda r: r.relative_url)

        table = Table("Relative url", "Target", "HTTP methods", "JWT", "CORS")
        for route in routes:
            jwt = "On" if route.jwt else "-"
            cors = "On" if route.cors else "-"
            http_methods = " ".join(route.http_methods) if route.http_methods else "All"
            table.add_row(route.relative_url, route.target, http_methods, jwt, cors)

        console.print(table)

    def get_routes(self) -> list[Route]:
        """Get all routes from Kong."""
        # Get routes
        resp = self._request(method="GET", url=self.routes_url)
        route_data = {r.get("name"): r for r in resp.json().get("data")}

        # Get services
        resp = self._request(method="GET", url=self.services_url)
        service_data = {s.get("name"): s for s in resp.json().get("data")}

        # Get plugins
        resp = self._request(method="GET", url=self.plugins_url)
        plugins_json = resp.json().get("data")

        # Work out which plugins apply to which routes
        route_plugins = defaultdict(list)
        for p in plugins_json:
            plugin_route = p.get("route")
            plugin_id = plugin_route.get("id") if plugin_route else None
            if plugin_id:
                route_plugins[plugin_id].append(p)

        routes = []
        for _, route_json in route_data.items():
            route_id = route_json["id"]
            route_name = route_json["name"]
            route_path = route_json["paths"][0]
            http_methods = route_json.get("methods")

            service = service_data.get(route_name)
            if not service:
                continue

            service_port = service["port"]
            service_host = service["host"]
            service_protocol = service["protocol"]
            service_url = f"{service_protocol}://{service_host}:{service_port}"

            r = Route(
                relative_url=route_path,
                target=service_url,
                http_methods=http_methods,
            )

            # Check if route has plugins installed
            # There will be an entry per route per plugin
            for p in route_plugins.get(route_id) or []:
                if p.get("name") == "jwt":
                    r.jwt = True
                elif p.get("name") == "cors":
                    r.cors = True

            routes.append(r)

        return routes

    def get_consumers(self) -> list[Consumer]:
        """Get all consumers from Kong."""
        resp = self._request(method="GET", url=self.consumers_url)
        consumer_data = resp.json().get("data")
        consumer_data.sort(key=lambda x: x["username"])

        return [Consumer.from_json(c) for c in consumer_data]

    def print_consumers(self) -> None:
        """Print all consumers."""
        consumers: list[Consumer] = self.get_consumers()

        table = Table("Consumer")
        for consumer in consumers:
            table.add_row(consumer.username)

        console.print(table)

    def delete_consumer(self, consumer_name: str) -> None:
        """Delete a consumer from Kong given its name."""
        consumer_url = f"{self.consumers_url}/{consumer_name}"
        self._request(method="DELETE", url=consumer_url)

    def add_consumer(self, consumer_name: str) -> None:
        """Add a consumer to Kong given its name."""
        consumer = Consumer(username=consumer_name)
        self._request(method="POST", url=self.consumers_url, json=consumer.json())

    def add_jwt_cred(self, consumer_name: str) -> JwtCredential:
        """Add a JWT credential to a consumer given its name."""
        jwt_url = f"{self.consumers_url}/{consumer_name}/jwt"

        resp = self._request(
            method="POST",
            url=jwt_url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        return JwtCredential.from_json(resp.json())

    def get_jwt_creds(self, consumer_name: str) -> list[JwtCredential]:
        """Get all JWT credentials for a consumer given its name."""
        jwt_url = f"{self.consumers_url}/{consumer_name}/jwt"

        resp = self._request(method="GET", url=jwt_url)
        creds_data = resp.json()["data"]
        return [JwtCredential.from_json(d) for d in creds_data]

    def print_jwt_creds(self, creds: list[JwtCredential]):
        """Print JWT credentials for a consumer."""

        table = Table("Algorithm", "Secret", "ISS")
        for cred in creds:
            table.add_row(cred.algorithm, cred.secret, cred.iss)

        console.print(table)

    def print_jwt_creds_for_consumer(self, consumer_name):
        creds = self.get_jwt_creds(consumer_name)
        self.print_jwt_creds(creds)

    def setup_global_kong_statsd_plugin(self) -> str:
        """Install the kong statsd plugin on the kong admin API.

        This plugin is used to send metrics to Cockpit.
        It is installed globally for all services.
        """
        plugins_url = self.admin_url + "/plugins"

        # Delete existing statsd plugin if it exists
        resp = self._request(method="GET", url=plugins_url)
        plugins = resp.json()["data"]
        for plugin in plugins:
            if plugin["name"] == "statsd":
                self._request(method="DELETE", url=f"{plugins_url}/{plugin['id']}")
                break

        # Install statsd plugin
        resp = self._request(
            method="POST",
            url=plugins_url,
            json={
                "name": "statsd",
                "config": {
                    "port": 8125,
                    "prefix": "kong",
                },
            },
        )
        body_json = resp.json()
        plugin_id = body_json["id"]
        return plugin_id
