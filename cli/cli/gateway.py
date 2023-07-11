import json

import requests
from loguru import logger
from requests.adapters import HTTPAdapter
from rich.table import Table
from urllib3 import Retry

from cli import conf
from cli.console import console
from cli.model import Consumer, JwtCredential, Route

MAX_RETRIES = 5


def response_hook(response: requests.Response, *_args, **_kwargs):
    """Response hook to log request and call raise_for_status."""
    req = response.request
    logger.debug(f"{req.method}: {req.url}")
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        try:  # Try to parse the body as JSON
            body_json = err.response.json()
            logger.error(f"Error: \n{json.dumps(body_json, indent=2)}")
        except json.decoder.JSONDecodeError:
            logger.error(f"Error: \n{err.response.text}")
        raise err


class GatewayManager:
    """Configure routes via the Kong admin API."""

    admin_url: str
    gateway_url: str

    def __init__(self):
        # Local local config
        self.config = conf.InfraConfiguration.load()

        admin_url = [
            self.config.protocol,
            "://",
            self.config.gw_admin_host,
        ]

        admin_port = self.config.gw_admin_port
        if admin_port:
            admin_url.extend([":", str(admin_port)])

        self.admin_url = "".join(admin_url)

        gateway_url = [
            self.config.protocol,
            "://",
            self.config.gw_host,
        ]

        gateway_port = self.config.gw_port
        if gateway_port:
            gateway_url.extend([":", str(gateway_port)])

        self.gateway_url = "".join(gateway_url)

        self.routes_url = self.admin_url + "/routes"
        self.services_url = self.admin_url + "/services"
        self.consumers_url = self.admin_url + "/consumers"

        self.token = self.config.gw_admin_token

        self._create_session()

    def _create_session(self):
        self.session = requests.Session()
        if self.token:
            self.session.headers["X-Auth-Token"] = self.token
        self.session.headers["Content-Type"] = "application/json"
        self.session.hooks["response"].append(response_hook)

        retries = Retry(
            total=MAX_RETRIES,
            backoff_factor=2,
            status=MAX_RETRIES,  # Status max retries
            # 403: retry for token refresh
            # 404: retry for Envoy service not found
            status_forcelist=[500, 404, 403],
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

    def add_route(self, route: Route) -> requests.Response:
        service_url = f"{self.services_url}/{route.name}"
        route_url = f"{self.routes_url}/{route.name}"

        resp = self.session.put(url=service_url, json=route.service_json())
        resp = self.session.put(url=route_url, json=route.route_json())

        plugins_url = f"{route_url}/plugins"
        if route.cors:
            try:
                self.session.post(url=plugins_url, json=route.cors_json())
            except requests.HTTPError:
                # TODO - avoid ignoring this, any way to create or update?
                pass

        if route.jwt:
            try:
                self.session.post(url=plugins_url, json=route.jwt_json())
            except requests.HTTPError:
                # TODO - avoid ignoring this, any way to create or update?
                pass

        return resp

    def delete_route(self, route: Route) -> requests.Response:
        self.session.delete(url=f"{self.routes_url}/{route.name}")
        resp = self.session.delete(url=f"{self.services_url}/{route.name}")
        return resp

    def print_routes(self) -> None:
        routes: list[Route] = self.get_routes()
        routes.sort(key=lambda r: r.relative_url)

        table = Table("RELATIVE URL", "TARGET", "HTTP METHODS", title="Gateway Routes")
        for r in routes:
            http_methods = " ".join(r.http_methods) if r.http_methods else "All"
            table.add_row(r.relative_url, r.target, http_methods)
        console.print(table)

    def get_routes(self) -> list[Route]:
        resp = self.session.get(url=self.routes_url)
        route_data = {r.get("name"): r for r in resp.json().get("data")}

        resp = self.session.get(url=self.services_url)
        service_data = {s.get("name"): s for s in resp.json().get("data")}

        routes = list()
        for _, r in route_data.items():
            route_name = r["name"]
            route_path = r["paths"][0]
            http_methods = r.get("methods")

            service = service_data.get(route_name)
            if not service:
                continue

            service_port = service["port"]
            service_host = service["host"]
            service_protocol = service["protocol"]
            service_url = f"{service_protocol}://{service_host}:{service_port}"

            routes.append(
                Route(
                    relative_url=route_path,
                    target=service_url,
                    http_methods=http_methods,
                )
            )

        return routes

    def get_consumers(self) -> list[Consumer]:
        resp = self.session.get(url=self.consumers_url)
        consumer_data = resp.json().get("data")
        consumer_data.sort(key=lambda x: x["username"])

        return [Consumer.from_json(c) for c in consumer_data]

    def print_consumers(self) -> None:
        consumers: list[Consumer] = self.get_consumers()

        table = Table("CONSUMER", title="Consumers")
        for c in consumers:
            table.add_row(c.username)
        console.print(table)

    def delete_consumer(self, consumer_name: str):
        consumer_url = f"{self.consumers_url}/{consumer_name}"
        resp = self.session.delete(url=consumer_url)
        resp.raise_for_status()

    def add_consumer(self, consumer_name):
        consumer = Consumer(username=consumer_name)
        resp = self.session.post(url=self.consumers_url, json=consumer.json())
        resp.raise_for_status()

    def add_jwt_cred(self, consumer_name: str) -> JwtCredential:
        jwt_url = f"{self.consumers_url}/{consumer_name}/jwt"

        resp = self.session.post(
            url=jwt_url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()

        return JwtCredential.from_json(resp.json())

    def get_jwt_creds(self, consumer_name: str) -> list[JwtCredential]:
        jwt_url = f"{self.consumers_url}/{consumer_name}/jwt"

        resp = self.session.get(url=jwt_url)
        resp.raise_for_status()

        creds_data = resp.json()["data"]
        return [JwtCredential.from_json(d) for d in creds_data]

    def print_jwt_creds(self, creds: list[JwtCredential]):
        """Print JWT credentials for a consumer."""

        table = Table("ALGORITHM", "SECRET", "ISS", title="JWT Credentials")
        for c in creds:
            table.add_row(c.algorithm, c.secret, c.iss)
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
        resp = self.session.get(plugins_url)
        plugins = resp.json()["data"]
        for plugin in plugins:
            if plugin["name"] == "statsd":
                self.session.delete(f"{plugins_url}/{plugin['id']}")

        # Install statsd plugin
        resp = self.session.post(
            plugins_url,
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
