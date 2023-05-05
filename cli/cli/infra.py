import click
import copy
import yaml
import time

from cli.conf import CONFIG_FILE

from scaleway import Client
from scaleway.container.v1beta1 import (
    ContainerV1Beta1API,
    ListNamespacesResponse,
    ListContainersResponse,
    ContainerHttpOption,
    ContainerPrivacy,
    ContainerProtocol,
    Container,
    ContainerStatus,
    Token,
    Namespace,
    NamespaceStatus,
)
from scaleway.rdb.v1 import (
    RdbV1API,
    ListInstancesResponse,
    Instance,
    ListDatabasesResponse,
    InstanceStatus,
)

API_REGION = "fr-par"

AWAIT_DELAY_SECONDS = 5
AWAIT_RETRIES = 60

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

DB_INSTANCE_NAME = "scw-sls-gw"
DB_ENGINE = "PostgreSQL-14"
DB_USERNAME = "kong"
DB_PASSWORD = "K0ngkongkong!"
DB_VOLUME_TYPE = "lssd"
DB_NODE_TYPE = "DB-DEV-S"
DB_VOLUME_SIZE = "5000000000"  # Expressed in bytes

# Name is fixed for Scaleway managed database
DB_DATABASE_NAME = "rdb"
DB_DATABASE_NAME_LOCAL = "kong"


class InfraManager(object):
    def __init__(self):
        # Initialise SCW client
        self.scw_client = Client.from_config_file_and_env(profile_name="dev")

        # Initi Scaleway APIs
        self.containers = ContainerV1Beta1API(self.scw_client)
        self.rdb = RdbV1API(self.scw_client)

    def set_up_config(self, is_local: bool):
        if is_local:
            config_data = {
                "protocol": "http",
                "gw_admin_host": "localhost",
                "gw_admin_port": "8001",
                "gw_admin_token": "",
                "gw_host": "localhost",
                "gw_port": "8080",
                "db_host": "localhost",
                "db_port": "5432",
                "db_name": DB_DATABASE_NAME_LOCAL,
            }
        else:
            admin_host = self.get_gateway_admin_endpoint()
            container_host = self.get_gateway_endpoint()

            instance = self._get_database_instance()
            if not instance:
                click.secho("No database instance found", fg="red", bold=True)
                raise click.Abort()

            token = self.create_admin_container_token()

            config_data = {
                "protocol": "https",
                "gw_admin_host": admin_host,
                "gw_admin_port": 8080,
                "gw_admin_token": token,
                "gw_host": container_host,
                "gw_port": 8080,
                "db_host": instance.endpoint.ip,
                "db_port": instance.endpoint.port,
                "db_name": DB_DATABASE_NAME,
            }

        with open(CONFIG_FILE, "w") as fh:
            yaml.safe_dump(config_data, fh)

    def _do_await(self, check_func):
        for r in range(AWAIT_RETRIES):
            if check_func():
                break

            click.secho(".", nl=False)

            time.sleep(AWAIT_DELAY_SECONDS)

    def _get_container(self, admin=False):
        namespace = self._get_namespace()
        if not namespace:
            click.secho("No namespace found", fg="red", bold=True)
            raise click.Abort()

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

    def _get_database_instance(self):
        instances: ListInstancesResponse = self.rdb.list_instances(region=API_REGION)

        for i in instances.instances:
            if i.name == DB_INSTANCE_NAME:
                return i

        return None

    def _get_namespace(self):
        namespaces: ListNamespacesResponse = self.containers.list_namespaces(
            region=API_REGION
        )

        for n in namespaces.namespaces:
            if n.name == CONTAINER_NAMESPACE:
                return n

        return None

    def get_gateway_endpoint(self):
        container = self._get_container()

        if not container:
            click.secho("No admin container found", fg="red", bold=True)
            raise click.Abort()

        return container.domain_name

    def get_gateway_admin_endpoint(self):
        container = self._get_admin_container()

        if not container:
            click.secho("No container found", fg="red", bold=True)
            raise click.Abort()

        return container.domain_name

    def create_db(self):
        instance = self._get_database_instance()

        if instance:
            click.secho(f"Database {DB_INSTANCE_NAME} already exists")
        else:
            click.secho(f"Creating database instance {DB_INSTANCE_NAME}")

            instance: Instance = self.rdb.create_instance(
                name=DB_INSTANCE_NAME,
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
        instance = self._get_database_instance()

        if not instance:
            click.secho("No database instance found", fg="red", bold=True)
            raise click.Abort()

        click.secho(f"Database status: {instance.status}", fg="green", bold=True)

    def _do_await_db(self):
        instance = self._get_database_instance()

        if not instance:
            return False

        if instance.status == InstanceStatus.ERROR:
            click.secho("Database in error", fg="red", bold="true")
            raise click.Abort()
        elif instance.status != InstanceStatus.READY:
            return False

        return True

    def await_db(self):
        self._do_await(self._do_await_db)

        click.secho("Database ready", fg="green", bold=True)

    def create_namespace(self):
        namespace = self._get_namespace()

        if namespace:
            click.secho("Namespace already exists")
            return

        click.secho(f"Creating namespace {CONTAINER_NAMESPACE}")
        self.containers.create_namespace(
            region=API_REGION,
            name=CONTAINER_NAMESPACE,
        )

    def check_namespace(self):
        namespace = self._get_namespace()

        if namespace is None:
            click.secho("No namespace found", fg="red", bold="true")
            raise click.Abort()

        if namespace.status == NamespaceStatus.ERROR:
            click.secho("Namespace in error", fg="red", bold="true")
            raise click.Abort()

        click.secho(f"Namespace status: {namespace.status}", fg="green", bold="true")

    def _do_await_namespace(self):
        namespace: Namespace = self._get_namespace()

        if not namespace:
            return False

        if namespace.status == NamespaceStatus.ERROR:
            click.secho("Namespace in error", fg="error", bold="true")
            raise click.Abort()
        elif namespace.status != NamespaceStatus.READY:
            return False

        return True

    def await_namespace(self):
        self._do_await(self._do_await_namespace)
        click.secho("Namespace ready", fg="green", bold=True)

    def delete_namespace(self):
        namespace = self._get_namespace()

        if namespace is None:
            return

        self.containers.delete_namespace(
            namespace_id=namespace.id, region=namespace.region
        )

    def _get_container_env_vars(self):
        instance = self._get_database_instance()
        if instance is None:
            click.secho("No database found", fg="red", bold="true")
            raise click.Abort()

        container_env_vars = {
            "KONG_PG_HOST": instance.endpoint.ip,
            "KONG_PG_PORT": f"{instance.endpoint.port}",
            "KONG_PG_DATABASE": DB_DATABASE_NAME,
            "KONG_PG_USER": DB_USERNAME,
            "KONG_PG_PASSWORD": DB_PASSWORD,
        }

        admin_container_env_vars = copy.copy(container_env_vars)
        admin_container_env_vars["IS_ADMIN_CONTAINER"] = "1"

        return admin_container_env_vars, container_env_vars

    def create_containers(self):
        namespace = self._get_namespace()
        if namespace is None:
            click.secho("No namespace found", fg="red", bold="true")
            raise click.Abort()

        admin_container_env_vars, container_env_vars = self._get_container_env_vars()

        admin_container = self._get_admin_container()
        if admin_container is not None:
            click.secho(
                f"Admin container {CONTAINER_ADMIN_NAME} already exists",
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
                environment_variables=admin_container_env_vars,
            )

            click.secho(f"Deploying container {CONTAINER_ADMIN_NAME}")

            self.containers.deploy_container(
                container_id=created_container.id, region=API_REGION
            )

        container = self._get_container()
        if container is not None:
            click.secho(f"Container {CONTAINER_NAME} already exists")
        else:
            click.secho(f"Creating container {CONTAINER_NAME}")

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
                environment_variables=container_env_vars,
            )

            click.secho(f"Deploying container {CONTAINER_NAME}")
            self.containers.deploy_container(
                container_id=created_container.id, region=API_REGION
            )

    def delete_containers(self):
        admin_container = self._get_admin_container()
        container = self._get_container()

        if admin_container:
            click.secho(f"Deleting container {CONTAINER_ADMIN_NAME}")
            self.containers.delete_container(
                container_id=admin_container.id, region=API_REGION
            )

        if container:
            click.secho(f"Deleting container {CONTAINER_NAME}")
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

        click.secho(f"Admin container status: {admin_container.status}")
        click.secho(f"Container status: {container.status}")

    def _do_await_containers(self):
        admin_container = self._get_admin_container()
        container = self._get_container()

        if not admin_container:
            return False

        if not container:
            return False

        if admin_container.status == ContainerStatus.ERROR:
            click.secho("Admin container in error", fg="red", bold=True)
            raise click.Abort()
        elif admin_container.status != ContainerStatus.READY:
            return False

        if container.status == ContainerStatus.ERROR:
            click.secho("Container in error", fg="red", bold=True)
            raise click.Abort()
        elif container.status != ContainerStatus.READY:
            return False

        return True

    def await_containers(self):
        self._do_await(self._do_await_containers)

        click.secho("Containers ready", fg="green", bold=True)

    def create_admin_container_token(self):
        admin_container = self._get_admin_container()

        if admin_container is None:
            click.secho("No admin container found", fg="red", bold="true")
            raise click.Abort()

        token: Token = self.containers.create_token(
            region=API_REGION, container_id=admin_container.id
        )

        return token.token

    def update_container(self):
        self.update_container_without_deploy()

        admin_container = self._get_admin_container()
        container = self._get_container()

        click.secho("Deploying admin container")
        self.containers.deploy_container(
            container_id=admin_container.id, region=API_REGION
        )

        click.secho("Deploying container")
        self.containers.deploy_container(container_id=container.id, region=API_REGION)

    def update_container_without_deploy(self):
        admin_container = self._get_admin_container()
        container = self._get_container()

        if not admin_container:
            click.secho("Admin container does not exist", fg="red", bold=True)
            raise click.Abort()

        if not container:
            click.secho("Container does not exist", fg="red", bold=True)
            raise click.Abort()

        container_admin_env_vars, container_env_vars = self._get_container_env_vars()

        click.secho("Updating admin container")

        self.containers.update_container(
            container_id=admin_container.id,
            privacy=ContainerPrivacy.PRIVATE,
            memory_limit=CONTAINER_ADMIN_MEMORY_LIMIT,
            min_scale=CONTAINER_ADMIN_MIN_SCALE,
            max_scale=CONTAINER_ADMIN_MAX_SCALE,
            protocol=ContainerProtocol.HTTP1,
            http_option=ContainerHttpOption.REDIRECTED,
            registry_image=IMAGE_TAG,
            environment_variables=container_admin_env_vars,
        )

        click.secho("Updating container")

        self.containers.update_container(
            container_id=container.id,
            privacy=ContainerPrivacy.PRIVATE,
            memory_limit=CONTAINER_MEMORY_LIMIT,
            min_scale=CONTAINER_MIN_SCALE,
            max_scale=CONTAINER_MAX_SCALE,
            protocol=ContainerProtocol.HTTP1,
            http_option=ContainerHttpOption.REDIRECTED,
            registry_image=IMAGE_TAG,
            environment_variables=container_env_vars,
        )

    def set_custom_domain(self):
        pass
