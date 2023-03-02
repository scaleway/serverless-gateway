import requests
import yaml
from loguru import logger


class KongConfig(object):
    """
    Wraps the Kong configuration.

    Uses the Kong admin API to load the config file from the running Kong instance,
    modify the config file in memory, then sent it back for Kong to hot reload.
    """

    def __init__(self, admin_url):
        # Set up URLs using plugin config passed in conf file
        self.admin_url = admin_url
        self.config_url = f"{self.admin_url}/config"

        # Load current config file from the Kong admin
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
        Sends the updated config to Kong for hot reload
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
