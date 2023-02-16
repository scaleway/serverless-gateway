#!/usr/bin/env python3
import json
import pprint

import kong_pdk.pdk.kong as kong
import requests
import yaml
from loguru import logger

PLUGIN_CONF_ADMIN_URL = "admin_url"
Schema = ({PLUGIN_CONF_ADMIN_URL: {"type": "string"}},)

VERSION = "0.1.0"

PRIORITY = 0

PLUGIN_NAME = "scw-sls-gw"

ROUTES_CONFIG_SECTION = "routes"
SERVICES_CONFIG_SECTION = "services"


class KongConfig(object):
    def __init__(self, admin_url):
        self.admin_url = admin_url
        self.config_url = f"{self.admin_url}/config"

        logger.debug(f"Loading config from {self.config_url}")
        response = requests.get(self.config_url)
        if response.status_code != requests.codes.ok:
            logger.error(
                f"Failed to load config with {response.status_code}: {response.text}"
            )
            raise RuntimeError()

        config_yaml = response.json().get("config")
        if len(config_yaml) == 0:
            logger.warn("Got no config back from admin API")

        self._conf = yaml.safe_load(config_yaml)
        pprint.pprint(self._conf, indent=2, compact=False)

    def get_endpoints(self):
        response = {
            "endpoints": list(),
        }

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

    def set_config(self):
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
        section_data = self._conf.get(section)
        if not section_data:
            logger.error(f"Section {section} not found in config")
            raise RuntimeError()

        return section_data

    def get_element(self, section, name):
        section_data = self.get_section(section)
        matches = [s for s in section_data if s.get("name") == name]
        if len(matches) == 0:
            return None

        return matches[0]

    def create_element(self, section, elem):
        # Delete if exists
        self.delete_element(section, elem)

        # Add and write
        self._conf[section].append(elem)

    def delete_element(self, section, elem):
        name = elem.get("name")
        section_data = self.get_section(section)

        # Remove all entries in this section matching on name
        section_data = [e for e in section_data if e["name"] != name]
        self._conf[section] = section_data


class Endpoint(object):
    @staticmethod
    def from_json(json_body):
        endpoint = Endpoint()
        endpoint.http_method = json_body.get("http_method")
        endpoint.target = json_body.get("target")

        endpoint.relative_url = json_body.get("relative_url")
        endpoint.name = endpoint.relative_url.replace("/", "_")

        endpoint.service = endpoint.build_service()
        endpoint.route = endpoint.build_route()

        return endpoint

    def validate(self):
        # TODO - validate operation and return error message
        pass

    def build_route(self):
        return {
            "name": self.name,
            "paths": [
                self.relative_url,
            ],
            "service": self.name,
        }

    def build_service(self):
        return {
            "name": self.name,
            "host": "localhost",
            "url": self.target,
        }

    def create(self, kong_conf):
        kong_conf.create_element(SERVICES_CONFIG_SECTION, self.service)
        kong_conf.create_element(ROUTES_CONFIG_SECTION, self.route)

        kong_conf.set_config()

    def delete(self, kong_conf):
        kong_conf.delete_element(ROUTES_CONFIG_SECTION, self.route)
        kong_conf.delete_element(SERVICES_CONFIG_SECTION, self.service)

        kong_conf.set_config()


class Plugin(object):
    def __init__(self, config):
        self.admin_url = config.get(PLUGIN_CONF_ADMIN_URL)
        self.kong_conf = KongConfig(self.admin_url)

    def access(self, kong: kong.kong):
        method = kong.request.get_method()

        kong.response.set_header("Content-Type", "application/json")

        if method == "GET":
            endpoints = self.kong_conf.get_endpoints()
            kong.response.exit(requests.codes.ok, json.dumps(endpoints))
            return

        elif method in ("POST", "DELETE"):
            body_data = kong.request.get_body()
            logger.info(f"SCW plugin got payload: {body_data}")

            endpoint = Endpoint.from_json(body_data)
            err_msg = endpoint.validate()
            if err_msg:
                kong.response.exit(
                    requests.codes.bad_request,
                    json.dumps({"message": f"Invalid request: {err_msg}"}),
                )
                return

            if method == "POST":
                err_msg = endpoint.create(self.kong_conf)
            else:
                err_msg = endpoint.delete(self.kong_conf)

            if err_msg:
                kong.response.exit(
                    requests.codes.server_error,
                    json.dumps({"message": f"Request failed: {err_msg}"}),
                )
                return

        else:
            logger.error(f"Unsupported HTTP method {method}")
            kong.response.exit(
                requests.codes.bad_request,
                json.dumps({"message": "Unsupported HTTP method"}),
            )
            return

        kong.response.exit(requests.codes.ok, json.dumps({"message": "Success"}))


if __name__ == "__main__":
    from kong_pdk.cli import start_dedicated_server

    start_dedicated_server(PLUGIN_NAME, Plugin, VERSION, PRIORITY, Schema)
