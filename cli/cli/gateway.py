import json
from typing import List

import click
import requests
from loguru import logger

from cli import conf
from cli.model import Route


def response_hook(response: requests.Response, *_args, **_kwargs):
    """Response hook to log request and call raise_for_status."""
    req = response.request
    logger.debug(f"{req.method}: {req.url}")
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        body_json = err.response.json()
        logger.error(f"Error: \n{json.dumps(body_json, indent=2)}")
        raise


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
        self.token = self.config.gw_admin_token

        self.session = requests.Session()
        if self.token:
            self.session.headers["X-Auth-Token"] = self.token
        self.session.headers["Content-Type"] = "application/json"
        self.session.hooks["response"].append(response_hook)

    def add_route(self, route: Route):
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

        return resp

    def delete_route(self, route: Route):
        self.session.delete(url=f"{self.routes_url}/{route.name}")
        resp = self.session.delete(url=f"{self.services_url}/{route.name}")
        return resp

    def print_routes(self):
        routes: List[Route] = self.get_routes()
        routes.sort(key=lambda r: r.relative_url)

        click.secho(
            f"{'RELATIVE URL':<25} {'TARGET':<40} {'HTTP_METHODS':<10}", bold=True
        )
        for r in routes:
            http_methods = r.http_methods if r.http_methods else "All"
            click.secho(f"{r.relative_url:<25} {r.target:<40} {http_methods:<10}")

    def get_routes(self) -> List[Route]:
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
