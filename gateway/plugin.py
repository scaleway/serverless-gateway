#!/usr/bin/env python3
import json

import kong_pdk.pdk.kong as kong
import requests
import yaml
from loguru import logger

# Plugin config according to the Kong PDK:
# https://github.com/Kong/kong-python-pdk
PLUGIN_CONF_ADMIN_URL = "admin_url"
Schema = ({PLUGIN_CONF_ADMIN_URL: {"type": "string"}},)
VERSION = "0.1.0"
PRIORITY = 0
PLUGIN_NAME = "scw-sls-gw"

# Config file constants
ROUTES_CONFIG_SECTION = "routes"
SERVICES_CONFIG_SECTION = "services"


# Class wrapping functionality around Kong configuration
class KongConfig(object):
    def __init__(self, admin_url):
        # Set up URLs
        self.admin_url = admin_url
        self.config_url = f"{self.admin_url}/config"

        # Load current config from Kong admin
        logger.debug(f"Loading config from {self.config_url}")
        response = requests.get(self.config_url)
        if response.status_code != requests.codes.ok:
            logger.error(
                f"Failed to load config with {response.status_code}: {response.text}"
            )
            raise RuntimeError()

        # Parse response and extract YAML
        config_yaml = response.json().get("config")
        if len(config_yaml) == 0:
            logger.warning("Got no config back from admin API")
        else:
            # Cache config YAML object
            self._conf = yaml.safe_load(config_yaml)

    def get_endpoints(self):
        """
        Returns list of existing endpoints
        """

        response = {
            "endpoints": list(),
        }

        # Iterate through contents of config file to extract endpoints
        routes = self.get_section("routes")
        for route in routes:
            service = self.get_element("services", route.get("name"))
            if not service:
                continue

            protocol = service.get("protocol")
            host = service.get("host")
            port = service.get("port")
            path = service.get("path")

            target = [
                f"{protocol}://",
                host,
                f":{port}" if port else "",
                f"{path}" if path else "",
            ]
            target = "".join(target)

            response["endpoints"].append(
                {
                    "http_methods": route.get("methods"),
                    "target": target,
                    "relative_url": route["paths"][0],
                }
            )

        return response

    def update_config(self):
        """
        Updates the config in Kong
        """
        response = requests.post(
            self.config_url,
            json={"config": yaml.dump(self._conf)},
        )

        if response.status_code not in (200, 201):
            logger.error(
                f"Failed to set new config {response.status_code}: {response.text}"
            )
            raise RuntimeError()

    def get_section(self, section):
        """
        Gets the given section from the config file
        """
        section_data = self._conf.get(section)
        if not section_data:
            logger.error(f"Section {section} not found in config")
            raise RuntimeError()

        return section_data

    def get_element(self, section, name):
        """
        Gets a specific element from the given section in the config file
        """
        section_data = self.get_section(section)
        matches = [s for s in section_data if s.get("name") == name]
        if len(matches) == 0:
            return None

        return matches[0]

    def create_element(self, section, elem):
        """
        Creates a new element in the given section in the config file
        """
        # Delete if exists
        self.delete_element(section, elem)

        # Add and write
        self._conf[section].append(elem)

    def delete_element(self, section, elem):
        """
        Deletes an element in the given section in the config file
        """
        name = elem.get("name")
        section_data = self.get_section(section)

        # Remove all entries in this section matching on name
        section_data = [e for e in section_data if e["name"] != name]
        self._conf[section] = section_data


# Class representing a function/container endpoint
class Endpoint(object):

    def __init__(self):
        self.http_method  = ""
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


# Main plugin object needed for the Kong PDK
class Plugin(object):
    def __init__(self, config):
        self.admin_url = config.get(PLUGIN_CONF_ADMIN_URL)
        self.kong_conf = KongConfig(self.admin_url)

    def access(self, kong: kong.kong):
        """
        Called whenever an endpoint bound to this plugin is accessed
        """
        method = kong.request.get_method()

        kong.response.set_header("Content-Type", "application/json")

        # Take action based on the HTTP method
        if method == "GET":
            # Return list of configured endpoints
            endpoints = self.kong_conf.get_endpoints()
            kong.response.exit(requests.codes.ok, bytes(json.dumps(endpoints), 'utf-8'), None)
            return

        elif method in ("POST", "DELETE"):
            # Extract body from request
            body_data = kong.request.get_body()
            logger.info(f"SCW plugin got payload: {body_data}")

            # Construct and validate an endpoint
            endpoint = Endpoint.from_json(body_data)
            err_msg = endpoint.validate()
            if err_msg:
                kong.response.exit(
                    status=requests.codes.bad_request, 
                    body=bytes(json.dumps({"message": f"Invalid request: {err_msg}"}), 'utf-8'),
                    headers=None
                )
                return

            # Delete or create endpoint depending on HTTP method
            if method == "DELETE":
                err_msg = endpoint.delete(self.kong_conf)
            else:
                err_msg = endpoint.create(self.kong_conf)

            if err_msg:
                kong.response.exit(
                    status=requests.codes.server_error,
                    body=bytes(json.dumps({"message": f"Request failed: {err_msg}"}), 'utf-8'),
                    headers=None
                )
                return

        else:
            # Handle unexpected HTTP method
            logger.error(f"Unsupported HTTP method {method}")
            kong.response.exit(
                status=requests.codes.bad_request,
                body=bytes(json.dumps({"message": "Unsupported HTTP method"}), 'utf-8'),
                headers=None
            )
            return

        # Exit successfully
        kong.response.exit(
            status=requests.codes.ok,
            body=bytes(json.dumps({"message": "Success"}), 'utf-8'), 
            headers=None
        )


if __name__ == "__main__":
    # Start server using Kong PDK
    from kong_pdk.cli import start_dedicated_server

    start_dedicated_server(PLUGIN_NAME, Plugin, VERSION, PRIORITY, Schema)
