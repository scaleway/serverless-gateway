import requests
from loguru import logger

from cli import conf
from cli.model import Route


def response_hook(response: requests.Response, *_args, **_kwargs):
    """Response hook to log request and call raise_for_status."""
    req = response.request
    logger.debug(f"{req.method}: {req.url}")
    response.raise_for_status()


class GatewayManager:
    """Configure routes via the Kong admin API."""

    def __init__(self):
        # Local local config
        self.config = conf.InfraConfiguration.load()

        self.admin_url = [
            self.config.protocol,
            "://",
            self.config.gw_admin_host,
        ]

        admin_port = self.config.gw_admin_port
        if admin_port:
            self.admin_url.extend([":", str(admin_port)])

        self.admin_url = "".join(self.admin_url)

        self.gateway_url = [
            self.config.protocol,
            "://",
            self.config.gw_host,
        ]

        gateway_port = self.config.gw_port
        if gateway_port:
            self.gateway_url.extend([":", str(gateway_port)])

        self.gateway_url = "".join(self.gateway_url)

        self.routes_url = self.admin_url + "/routes"
        self.services_url = self.admin_url + "/services"
        self.token = self.config.gw_admin_token

        self.session = requests.Session()
        self.session.headers["X-Auth-Token"] = self.token
        self.session.hooks["response"].append(response_hook)

    def add_route(self, route: Route):
        service_url = f"{self.services_url}/{route.name}"
        route_url = f"{self.routes_url}/{route.name}"

        self.session.put(url=service_url, data=route.service_json())
        resp = self.session.put(url=route_url, data=route.route_json())

        if route.cors:
            plugins_url = f"{route_url}/plugins"

            try:
                self.session.post(url=plugins_url, data=route.cors_json())
            except requests.HTTPError:
                # TODO - avoid ignoring this, any way to create or update?
                pass

        return resp

    def delete_route(self, route: Route):
        self.session.delete(url=f"{self.routes_url}/{route.name}")
        resp = self.session.delete(url=f"{self.services_url}/{route.name}")
        return resp

    def get_routes(self):
        resp = self.session.get(url=self.routes_url)
        route_data = {r.get("name"): r for r in resp.json().get("data")}

        resp = self.session.get(url=self.services_url)
        service_data = {s.get("name"): s for s in resp.json().get("data")}

        routes = list()
        for _, r in route_data.items():
            route_name = r["name"]
            route_paths = r["paths"]
            http_methods = r.get("methods")

            service = service_data.get(route_name)
            if not service:
                continue

            service_port = service["port"]
            service_host = service["host"]
            service_protocol = service["protocol"]
            service_url = f"{service_protocol}://{service_host}:{service_port}"

            routes.append(Route(route_paths, service_url, http_methods=http_methods))

        return routes
