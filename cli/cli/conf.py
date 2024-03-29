import os
import typing as t
from dataclasses import asdict, dataclass

import click
import yaml

from cli.console import console

if t.TYPE_CHECKING:
    # Importing conditionally to avoid circular imports
    from cli.infra import InfraManager

USER_HOME = os.path.expanduser("~")
CONFIG_DIR = os.path.join(USER_HOME, ".config", "scw")
CONFIG_FILE = os.path.join(CONFIG_DIR, "gateway.yml")

# Name is fixed for all managed databases
DB_DATABASE_NAME = "rdb"
DB_DATABASE_NAME_LOCAL = "kong"

# Default time to wait for resources
RESOURCE_AWAIT_TIMEOUT_MINUTES = 15
RESOURCE_AWAIT_TIMEOUT_SECONDS = 60 * RESOURCE_AWAIT_TIMEOUT_MINUTES


def _check_config_file():
    if not os.path.exists(CONFIG_FILE):
        console.print(
            "No gateway config file found. Have you run your gateway setup? Try:",
            style="red",
        )
        console.print("scwgw infra deploy", style="bold red")
        raise click.Abort()


@dataclass
class InfraConfiguration:
    """Configuration used to store information of a deployed gateway."""

    protocol: t.Literal["http", "https"]
    gw_admin_host: str
    gw_admin_port: str
    gw_admin_token: str
    gw_host: str
    gw_port: str
    db_host: str
    db_port: str
    db_name: str

    @staticmethod
    def from_local() -> "InfraConfiguration":
        """Get the configuration for the local docker-compose stack."""
        return InfraConfiguration(
            protocol="http",
            gw_admin_host="localhost",
            gw_admin_port="8001",
            gw_admin_token="",
            gw_host="localhost",
            gw_port="8080",
            db_host="localhost",
            db_port="5432",
            db_name=DB_DATABASE_NAME_LOCAL,
        )

    @staticmethod
    def from_infra(manager: "InfraManager") -> "InfraConfiguration":
        admin_host = manager.get_gateway_admin_endpoint()
        container_host = manager.get_gateway_endpoint()

        instance = manager._get_database_instance_or_abort()
        endpoint = instance.endpoints[0]

        token = manager.create_admin_container_token()

        return InfraConfiguration(
            protocol="https",
            gw_admin_host=admin_host,
            gw_admin_port="",
            gw_admin_token=token,
            gw_host=container_host,
            gw_port="",
            db_host=str(endpoint.ip),
            db_port=str(endpoint.port),
            db_name=DB_DATABASE_NAME,
        )

    @staticmethod
    def load() -> "InfraConfiguration":
        """Read the configuration from the config file."""

        _check_config_file()

        with open(CONFIG_FILE, mode="rt", encoding="utf-8") as file:
            conf = yaml.safe_load(file)
            return InfraConfiguration(**conf)

    @property
    def gw_url(self):
        gateway_url = [
            self.protocol,
            "://",
            self.gw_host,
        ]

        gateway_port = self.gw_port
        if gateway_port:
            gateway_url.extend([":", str(gateway_port)])

        return "".join(gateway_url)

    @property
    def gw_admin_url(self):
        admin_url = [
            self.protocol,
            "://",
            self.gw_admin_host,
        ]

        admin_port = self.gw_admin_port
        if admin_port:
            admin_url.extend([":", str(admin_port)])

        return "".join(admin_url)

    def save(self) -> None:
        """Save the configuration to a file."""
        os.makedirs(CONFIG_DIR, exist_ok=True)

        with open(CONFIG_FILE, mode="wt", encoding="utf-8") as file:
            yaml.safe_dump(asdict(self), file)
