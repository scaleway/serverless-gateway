import click

from scaleway import Client
from scaleway.container.v1beta1 import (
    ContainerV1Beta1API,
    ListNamespacesResponse,
    ListContainersResponse,
    ContainerHttpOption,
    ContainerPrivacy,
    ContainerProtocol,
    Container,
    Token,
)
from scaleway.rdb.v1 import RdbV1API, ListInstancesResponse

API_REGION = "fr-par"

IMAGE_REGISTRY = "docker.io"
IMAGE_ORG = "scaleway"
IMAGE_NAME = "serverless-gateway"
IMAGE_VERSION = "0.1.1"
IMAGE_TAG = f"{IMAGE_REGISTRY}/{IMAGE_ORG}/{IMAGE_NAME}:{IMAGE_VERSION}"

CONTAINER_NAMESPACE = "scw-sls-gw"

CONTAINER_NAME = "scw-sls-gw"
CONTAINER_MIN_SCALE = 1
CONTAINER_MAX_SCALE = 5
CONTAINER_MEMORY_LIMIT = 1024

CONTAINER_ADMIN_NAME = "scw-sls-gw-admin"
CONTAINER_ADMIN_MIN_SCALE = 1
CONTAINER_ADMIN_MAX_SCALE = 1
CONTAINER_ADMIN_MEMORY_LIMIT = 1024

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

    def _get_container(self, admin=False):
        namespace = self._get_namespace()

        containers: ListContainersResponse = self.containers.list_containers(
            namespace_id=namespace.id, region=API_REGION
        )

        for c in containers.containers:
            if admin and c.name == CONTAINER_ADMIN_NAME:
                return c
            elif c.name == CONTAINER_NAME:
                return c

        return None

    def _get_admin_container(self):
        return self._get_container(admin=True)

    def _get_database(self):
        databases: ListInstancesResponse = self.rdb.list_instances(region=API_REGION)

        for d in databases.instances:
            if d.name == DB_NAME:
                return d

        return None

    def _get_namespace(self):
        namespaces: ListNamespacesResponse = self.containers.list_namespaces(
            region=API_REGION
        )

        for n in namespaces.namespaces:
            if n.name == CONTAINER_NAMESPACE:
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
            raise click.Abort()

        click.secho(f"Database status: {db.status}", fg="green", bold=True)

    def create_namespace(self):
        namespace = self._get_namespace()

        if namespace:
            click.secho("Namespace already exists")
            return

        click.secho(f"Creating namespace {CONTAINER_NAMESPACE}", fg="green", bold=True)
        self.containers.create_namespace(
            region=API_REGION,
            name=CONTAINER_NAMESPACE,
        )

    def check_namespace(self):
        namespace = self._get_namespace()

        if namespace is None:
            click.secho("No namespace found", fg="red", bold="true")
            raise click.Abort()

        click.secho(f"Namespace status: {namespace.status}", fg="green", bold="true")

    def delete_namespace(self):
        namespace = self._get_namespace()

        if namespace is None:
            return

        self.containers.delete_namespace(
            namespace_id=namespace.id, region=namespace.region
        )

    def create_containers(self):
        namespace = self._get_namespace()
        if namespace is None:
            click.secho("No namespace found", fg="red", bold="true")
            raise click.Abort()

        admin_container = self._get_admin_container()
        if admin_container is not None:
            click.secho(
                f"Admin container {CONTAINER_ADMIN_NAME} already exists",
                fg="green",
                bold="true",
            )
        else:
            click.secho(
                f"Creating admin container {CONTAINER_ADMIN_NAME}",
                fg="green",
                bold="true",
            )

            created_container: Container = self.containers.create_container(
                namespace_id=namespace.id,
                name=CONTAINER_ADMIN_NAME,
                memory_limit=CONTAINER_ADMIN_MEMORY_LIMIT,
                min_scale=CONTAINER_ADMIN_MIN_SCALE,
                max_scale=CONTAINER_ADMIN_MAX_SCALE,
                privacy=ContainerPrivacy.PRIVATE,
                protocol=ContainerProtocol.HTTP1,
                http_option=ContainerHttpOption.REDIRECTED,
                registry_image=IMAGE_TAG,
            )

            click.secho(
                f"Deploying container {CONTAINER_ADMIN_NAME}",
                fg="green",
                bold="true",
            )

            self.containers.deploy_container(
                container_id=created_container.id, region=API_REGION
            )

        container = self._get_container()
        if container is not None:
            click.secho(
                f"Container {CONTAINER_NAME} already exists",
                fg="green",
                bold="true",
            )
        else:
            click.secho(
                f"Creating container {CONTAINER_NAME}",
                fg="green",
                bold="true",
            )

            created_container: Container = self.containers.create_container(
                namespace_id=namespace.id,
                name=CONTAINER_NAME,
                memory_limit=CONTAINER_MEMORY_LIMIT,
                min_scale=CONTAINER_MIN_SCALE,
                max_scale=CONTAINER_MAX_SCALE,
                privacy=ContainerPrivacy.PUBLIC,
                protocol=ContainerProtocol.HTTP1,
                http_option=ContainerHttpOption.REDIRECTED,
                registry_image=IMAGE_TAG,
            )

            click.secho(
                f"Deploying container {CONTAINER_NAME}",
                fg="green",
                bold="true",
            )
            self.containers.deploy_container(
                container_id=created_container.id, region=API_REGION
            )

    def delete_containers(self):
        admin_container = self._get_admin_container()
        container = self._get_container()

        if admin_container:
            click.secho(
                f"Delete container {CONTAINER_ADMIN_NAME}",
                fg="green",
                bold="true",
            )
            self.containers.delete_container(
                container_id=admin_container.id, region=API_REGION
            )

        if container:
            click.secho(
                f"Delete container {CONTAINER_NAME}",
                fg="green",
                bold="true",
            )
            self.containers.delete_container(
                container_id=container.id, region=API_REGION
            )

    def check_containers(self):
        admin_container = self._get_admin_container()
        container = self._get_container()

        if admin_container is None:
            click.secho("No admin container found", fg="red", bold="true")

        if container is None:
            click.secho("No container found", fg="red", bold="true")

        if admin_container is None or container is None:
            raise click.Abort()

        click.secho(
            f"Admin container status: {admin_container.status}", fg="green", bold="true"
        )
        click.secho(f"Container status: {container.status}", fg="green", bold="true")

    def create_admin_container_token(self):
        admin_container = self._get_admin_container()

        if admin_container is None:
            click.secho("No admin container found", fg="red", bold="true")
            raise click.Abort()

        token: Token = self.containers.create_token(
            region=API_REGION, container_id=admin_container.id
        )

        return token.token

    def set_custom_domain(self):
        pass

    def update_container(self):
        pass

    def update_container_without_deploy(self):
        pass
