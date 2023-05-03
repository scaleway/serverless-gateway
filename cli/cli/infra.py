import click

from scaleway import Client
from scaleway.container.v1beta1 import ContainerV1Beta1API, ListNamespacesResponse
from scaleway.rdb.v1 import RdbV1API, ListInstancesResponse

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

    def _get_database(self):
        databases: ListInstancesResponse = self.rdb.list_instances(
            region=SCW_API_REGION
        )

        for d in databases.instances:
            if d.name == DB_NAME:
                return d

        return None

    def _get_namespace(self):
        namespaces: ListNamespacesResponse = self.containers.list_namespaces(
            region=SCW_API_REGION
        )

        for n in namespaces.namespaces:
            if n.name == SCW_CONTAINER_NAMESPACE:
                return n

        return None

    def get_gateway_host(self):
        pass

    def get_gateway_admin_host(self):
        pass

    def create_db(self):
        db = self._get_database()

        if db:
            click.secho(f"Database {DB_NAME} already exists", fg="green", bold=True)
            return

        click.secho(f"Creating database {DB_NAME}", fg="green", bold=True)

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

    def check_db(self):
        db = self._get_database()

        if not db:
            click.secho("No database found", fg="red", bold=True)
            return

        click.secho(f"Database status: {db.status}", fg="green", bold=True)

    def create_namespace(self):
        namespace = self._get_namespace()

        if namespace:
            click.secho("Namespace already exists")
            return

        click.secho(
            f"Creating namespace {SCW_CONTAINER_NAMESPACE}", fg="green", bold=True
        )
        self.containers.create_namespace(
            region=SCW_API_REGION,
            name=SCW_CONTAINER_NAMESPACE,
        )

    def check_namespace(self):
        namespace = self._get_namespace()

        if namespace is None:
            click.secho("No namespace found", fg="red", bold="true")
            return

        click.secho(f"Namespace status: {namespace.status}", fg="green", bold="true")

    def delete_namespace(self):
        namespace = self._get_namespace()

        if namespace is None:
            return

        self.containers.delete_namespace(
            namespace_id=namespace.id, region=namespace.region
        )

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
