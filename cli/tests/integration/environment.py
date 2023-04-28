import os
from dataclasses import dataclass


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
        func_a_url = f'https://{os.environ["FUNC_A_DOMAIN"]}:443'
        gw_admin_url = f'https://{os.environ["GATEWAY_ADMIN_HOST"]}:443'
        gw_url = f'https://{os.environ["GATEWAY_HOST"]}:443'

        return IntegrationEnvironment(
            gw_admin_url=gw_admin_url,
            gw_routes_url=gw_admin_url + "/routes",
            gw_url=gw_url,
            host_func_a_url=func_a_url,
            gw_func_a_url=func_a_url,
        )
