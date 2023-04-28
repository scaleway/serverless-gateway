from scaleway import Client
from scaleway.container.v1beta1 import ContainerV1Beta1API

SCW_API_REGION = "fr-par"

SCW_CONTAINER_NAMESPACE = "scw-sls-gw"
SCW_CONTAINER_NAME = "scw-sls-gw"
SCW_CONTAINER_MIN_SCALE = 1
SCW_CONTAINER_MEMORY_LIMIT = 1024


class InfraManager(object):
    def __init__(self):
        # Initialise SCW client
        self.scw_client = Client.from_config_file_and_env(profile_name="dev")

        # Initi Scaleway APIs
        self.containers = ContainerV1Beta1API(self.scw_client)

    def _get_container_id(self):
        pass

    def _get_namespace_id(self):
        pass

    def get_gateway_host(self):
        pass

    def get_gateway_admin_host(self):
        pass

    def create_db(self):
        pass

    def create_namespace(self):
        pass

    def check_namespace(self):
        pass

    def delete_namespace(self):
        pass

    def create_containers(self):
        pass

    def delete_containers(self):
        pass

    def check_containers(self):
        pass

    def set_custom_domain(self):
        pass

    def update_container(self):
        pass

    def update_container_without_deploy(self):
        pass
