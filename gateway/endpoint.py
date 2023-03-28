from typing import Any

# Config file constants
ROUTES_CONFIG_SECTION = "routes"
SERVICES_CONFIG_SECTION = "services"


class Endpoint(object):
    """
    Represents a function/container endpoint
    """

    def __init__(self):
        self.http_methods: list[str] = []
        self.target = ""
        self.relative_url = ""
        self.name = ""
        self.service = {}
        self.route = {}
        self.built_in_plugins = [{
                        "name": "cors", 
                        "config": {
                            "origins": ["*"],
                            "headers": ["*"],
                            "credentials": True
                        }
        }]

    @staticmethod
    def from_json(json_body: dict[str, Any]):
        """
        Parses an endpoint from a JSON input
        """
        endpoint = Endpoint()
        endpoint.http_methods = json_body.get("http_methods", [])
        endpoint.target = json_body.get("target", "")

        endpoint.relative_url = json_body.get("relative_url", "")
        endpoint.name = endpoint.relative_url.replace("/", "_")

        endpoint.service = endpoint.build_service()
        endpoint.route = endpoint.build_route()

        return endpoint

    def validate(self):
        """
        Validates the endpoint configuration
        """
        # TODO - validate operation and return error message
        pass

    def build_route(self):
        """
        Builds the Kong route definition for this endpoint
        """
        route = {
            "name": self.name,
            "paths": [
                self.relative_url,
            ],
            "service": self.name,
        }
        if self.http_methods:
            route["methods"] = self.http_methods
        return route

    def build_service(self):
        """
        Builds the Kong service definition for this endpoint
        """
        return {
            "name": self.name,
            "host": "localhost",
            "url": self.target,
            "plugins": self.built_in_plugins
        }

    def create(self, kong_conf):
        """
        Creates this endpoint in the config, and updates Kong
        """
        kong_conf.create_element(SERVICES_CONFIG_SECTION, self.service, True)
        kong_conf.create_element(ROUTES_CONFIG_SECTION, self.route, True)

        kong_conf.update_config()

    def delete(self, kong_conf):
        """
        Deletes this endpoint from the config, and updates Kong
        """
        kong_conf.delete_element(ROUTES_CONFIG_SECTION, self.route)
        kong_conf.delete_element(SERVICES_CONFIG_SECTION, self.service)

        kong_conf.update_config()
