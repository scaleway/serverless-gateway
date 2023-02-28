# Config file constants
ROUTES_CONFIG_SECTION = "routes"
SERVICES_CONFIG_SECTION = "services"


# Class representing a function/container endpoint
class Endpoint(object):
    def __init__(self):
        self.http_method = ""
        self.target = ""
        self.relative_url = ""
        self.name = ""
        self.service = {}
        self.route = {}

    @staticmethod
    def from_json(json_body):
        """
        Parses an endpoint from a JSON input
        """
        endpoint = Endpoint()
        endpoint.http_method = json_body.get("http_method")
        endpoint.target = json_body.get("target")

        endpoint.relative_url = json_body.get("relative_url")
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
        return {
            "name": self.name,
            "paths": [
                self.relative_url,
            ],
            "service": self.name,
        }

    def build_service(self):
        """
        Builds the Kong service definition for this endpoint
        """
        return {
            "name": self.name,
            "host": "localhost",
            "url": self.target,
        }

    def create(self, kong_conf):
        """
        Creates this endpoint in the config, and updates Kong
        """
        kong_conf.create_element(SERVICES_CONFIG_SECTION, self.service)
        kong_conf.create_element(ROUTES_CONFIG_SECTION, self.route)

        kong_conf.update_config()

    def delete(self, kong_conf):
        """
        Deletes this endpoint from the config, and updates Kong
        """
        kong_conf.delete_element(ROUTES_CONFIG_SECTION, self.route)
        kong_conf.delete_element(SERVICES_CONFIG_SECTION, self.service)

        kong_conf.update_config()
