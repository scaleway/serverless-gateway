from scaleway import Client
from scaleway.container.v1beta1 import ContainerV1Beta1API
from scaleway.rdb.v1 import RdbV1API

SCW_API_REGION = "fr-par"

SCW_CONTAINER_NAMESPACE = "scw-sls-gw"
SCW_CONTAINER_NAME = "scw-sls-gw"
SCW_CONTAINER_MIN_SCALE = 1
SCW_CONTAINER_MEMORY_LIMIT = 1024

# Useful docs:
# RDB API - https://www.scaleway.com/en/developers/api/managed-database-postgre-mysql/
# Python SDK - https://github.com/scaleway/scaleway-sdk-python

DB_NAME = "scw-sls-gw"
DB_ENGINE = "PostgreSQL-14"
DB_USERNAME = "kong"
DB_PASSWORD = "K0ngkongkong!"
DB_VOLUME_TYPE = "lssd"
DB_NODE_TYPE = "DB-DEV-S"
DB_VOLUME_SIZE = "5000000000"  # Expressed in bytes


class InfraManager(object):
    def __init__(self):
        # Initialise SCW client
        self.scw_client = Client.from_config_file_and_env(profile_name="dev")

        # Initi Scaleway APIs
        self.containers = ContainerV1Beta1API(self.scw_client)
        self.rdb = RdbV1API(self.scw_client)

    def _get_container_id(self):
        pass

    def _get_namespace_id(self):
        pass

    def get_gateway_host(self):
        pass

    def get_gateway_admin_host(self):
        pass

    def create_db(self):
        self.rdb.create_instance(
            name=DB_NAME,
            engine=DB_ENGINE,
            user_name=DB_USERNAME,
            password=DB_PASSWORD,
            is_ha_cluster=False,
            disable_backup=True,
            backup_same_region=True,
            node_type=DB_NODE_TYPE,
            volume_type=DB_VOLUME_TYPE,
            volume_size=DB_VOLUME_SIZE,
        )

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
