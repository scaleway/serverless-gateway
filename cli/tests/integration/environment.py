from dataclasses import dataclass

from cli.client import get_scaleway_client
from cli.infra import InfraManager

FUNC_FIXTURE_NAME = "func-a"
FUNC_FIXTURE_NAMESPACE = "function-fixtures"


@dataclass
class IntegrationEnvironment:
    gw_admin_url: str
    gw_routes_url: str
    gw_url: str

    # The disitinction of those two variables is relevant for docker compose
    # URL of the function visible from our host
    host_func_a_url: str
    # URL of the function visible from the gateway
    gw_func_a_url: str

    # S3 bucket
    @staticmethod
    def get_docker_compose_env():
        gw_admin_url = "http://localhost:8001"
        gw_url = "http://localhost:8080"

        return IntegrationEnvironment(
            gw_admin_url=gw_admin_url,
            gw_routes_url=gw_admin_url + "/routes",
            gw_url=gw_url,
            host_func_a_url="http://localhost:8004",
            gw_func_a_url="http://func-a:80",
        )

    @staticmethod
    def get_scw_env():
        scw_client = get_scaleway_client()
        manager = InfraManager(scw_client=scw_client)

        func_a_endpoint = manager.get_function_endpoint(
            FUNC_FIXTURE_NAMESPACE, FUNC_FIXTURE_NAME
        )
        func_a_url = f"https://{func_a_endpoint}:443"

        gw_admin_endpoint = manager.get_gateway_admin_endpoint()
        gw_admin_url = f"https://{gw_admin_endpoint}:443"

        gw_endpoint = manager.get_gateway_endpoint()
        gw_url = f"https://{gw_endpoint}:443"

        return IntegrationEnvironment(
            gw_admin_url=gw_admin_url,
            gw_routes_url=gw_admin_url + "/routes",
            gw_url=gw_url,
            host_func_a_url=func_a_url,
            gw_func_a_url=func_a_url,
        )
