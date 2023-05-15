import copy
from concurrent import futures

import click
import scaleway.container.v1beta1 as cnt
import scaleway.function.v1beta1 as fnc
import scaleway.rdb.v1 as rdb
from scaleway import Client

from cli import conf

AWAIT_DELAY_SECONDS = 5
AWAIT_RETRIES = 60

IMAGE_REGISTRY = "docker.io"
IMAGE_ORG = "scaleway"
IMAGE_NAME = "serverless-gateway"
IMAGE_VERSION = "0.1.2"
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
DB_VOLUME_TYPE = "lssd"
DB_NODE_TYPE = "DB-DEV-S"
DB_VOLUME_SIZE = 5000000000  # Expressed in bytes

# Name is fixed for Scaleway managed database
DB_DATABASE_NAME = "rdb"


class InfraManager:
    """Manager for the infrastructure of the gateway."""

    def __init__(self, scw_client: Client):
        # Initialise SCW client
        self.scw_client = scw_client

        # Init Scaleway APIs
        self.containers = cnt.ContainerV1Beta1API(self.scw_client)
        self.functions = fnc.FunctionV1Beta1API(self.scw_client)
        self.rdb = rdb.RdbV1API(self.scw_client)

    def set_up_config(self, is_local: bool) -> None:
        """Set up the configuration for the gateway.

        Used by the GatewayManager to set up the route configuration.
        """
        if is_local:
            config = conf.InfraConfiguration.from_local()
        else:
            config = conf.InfraConfiguration.from_infra(self)
        config.save()

    def _get_container(self, admin=False) -> cnt.Container | None:
        namespace = self._get_namespace()
        if not namespace:
            click.secho("No namespace found", fg="red", bold=True)
            raise click.Abort()

        container_name = CONTAINER_ADMIN_NAME if admin else CONTAINER_NAME
        containers = self.containers.list_containers_all(
            namespace_id=namespace.id,
            name=container_name,
        )

        return containers[0] if containers else None

    def _get_admin_container(self) -> cnt.Container | None:
        return self._get_container(admin=True)

    def _get_container_or_abort(self, admin: bool = False) -> cnt.Container:
        container = self._get_container()
        if not container:
            container_name = "Admin" if admin else "Gateway"
            click.secho(
                f"{container_name} container not found"
                "Run `scw-gw create-containers` to deploy the gateway",
                fg="red",
                bold=True,
            )
            raise click.Abort()
        return container

    def _get_admin_container_or_abort(self) -> cnt.Container:
        return self._get_container_or_abort(admin=True)

    def _get_database_instance(self) -> rdb.Instance | None:
        instances = self.rdb.list_instances_all(name=DB_INSTANCE_NAME)
        return instances[0] if instances else None

    def _get_namespace(self):
        namespaces = self.containers.list_namespaces_all(name=CONTAINER_NAMESPACE)
        return namespaces[0] if namespaces else None

    def get_function_endpoint(self, namespace_name, function_name) -> str | None:
        namespaces = self.functions.list_namespaces_all(
            name=namespace_name,
        )
        if not namespaces:
            click.secho("No namespace found", fg="red", bold=True)
            raise click.Abort()

        namespace = namespaces[0]
        functions = self.functions.list_functions_all(
            namespace_id=namespace.id, name=function_name
        )

        return functions[0].domain_name if functions else None

    def get_gateway_endpoint(self) -> str:
        container = self._get_container_or_abort()
        return container.domain_name

    def get_gateway_admin_endpoint(self) -> str:
        container = self._get_admin_container_or_abort()
        return container.domain_name

    def create_db(self, password: str) -> None:
        instance = self._get_database_instance()

        if instance:
            click.secho(f"Database {DB_INSTANCE_NAME} already exists")
        else:
            click.secho(f"Creating database instance {DB_INSTANCE_NAME}")

            instance = self.rdb.create_instance(
                name=DB_INSTANCE_NAME,
                engine=DB_ENGINE,
                user_name=DB_USERNAME,
                password=password,
                is_ha_cluster=False,
                disable_backup=True,
                backup_same_region=True,
                node_type=DB_NODE_TYPE,
                volume_type=rdb.VolumeType(DB_VOLUME_TYPE),
                volume_size=DB_VOLUME_SIZE,
            )

    def check_db(self):
        instance = self._get_database_instance()

        if not instance:
            click.secho("No database instance found", fg="red", bold=True)
            raise click.Abort()

        click.secho(f"Database status: {instance.status}", fg="green", bold=True)

    def await_db(self) -> None:
        instance = self._get_database_instance()

        if not instance:
            click.secho("No database instance found", fg="red", bold=True)
            raise click.Abort()

        instance = self.rdb.wait_for_instance(instance_id=instance.id)
        if instance.status is not rdb.InstanceStatus.READY:
            click.secho("Database is not ready", fg="red", bold="true")
            raise click.Abort()

        click.secho("Database ready", fg="green", bold=True)

    def create_namespace(self):
        namespace = self._get_namespace()

        if namespace:
            click.secho("Namespace already exists")
            return

        click.secho(f"Creating namespace {CONTAINER_NAMESPACE}")
        self.containers.create_namespace(
            name=CONTAINER_NAMESPACE,
        )

    def check_namespace(self):
        namespace = self._get_namespace()

        if namespace is None:
            click.secho("No namespace found", fg="red", bold="true")
            raise click.Abort()

        if namespace.status == cnt.NamespaceStatus.ERROR:
            click.secho("Namespace in error", fg="red", bold="true")
            raise click.Abort()

        click.secho(f"Namespace status: {namespace.status}")

    def await_namespace(self):
        namespace = self._get_namespace()

        if not namespace:
            click.secho("No namespace found", fg="red", bold="true")
            raise click.Abort()

        namespace = self.containers.wait_for_namespace(namespace_id=namespace.id)
        if namespace.status == cnt.NamespaceStatus.ERROR:
            click.secho(
                f"Namespace in error: {namespace.error_message}",
                fg="error",
                bold="true",
            )
            raise click.Abort()

        click.secho("Namespace ready", fg="green", bold=True)

    # refactor this
    def delete_namespace(self):
        namespace = self._get_namespace()

        if namespace is None:
            return

        self.containers.delete_namespace(
            namespace_id=namespace.id, region=namespace.region
        )

    def _get_container_env_vars(self) -> tuple[dict[str, str], dict[str, str]]:
        instance = self._get_database_instance()
        if instance is None:
            click.secho("No database found", fg="red", bold="true")
            raise click.Abort()

        endpoint = instance.endpoints[0]
        host = endpoint.ip or endpoint.hostname
        if not host:
            raise ValueError("No database host found")

        container_env_vars = {
            "KONG_PG_HOST": host,
            "KONG_PG_PORT": str(endpoint.port),
            "KONG_PG_DATABASE": DB_DATABASE_NAME,
            "KONG_PG_USER": DB_USERNAME,
        }

        admin_container_env_vars = copy.copy(container_env_vars)
        admin_container_env_vars["IS_ADMIN_CONTAINER"] = "1"

        return admin_container_env_vars, container_env_vars

    def _get_container_secret_env_vars(self, db_password: str) -> list[cnt.Secret]:
        return [cnt.Secret("KONG_PG_PASSWORD", db_password)]

    def create_containers(self, db_password: str) -> None:
        """Create containers for Kong and Kong Admin."""

        namespace = self._get_namespace()
        if namespace is None:
            click.secho("No namespace found", fg="red", bold="true")
            raise click.Abort()

        admin_container_env_vars, container_env_vars = self._get_container_env_vars()
        secret_env_vars = self._get_container_secret_env_vars(db_password)

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

            created_container = self.containers.create_container(
                namespace_id=namespace.id,
                name=CONTAINER_ADMIN_NAME,
                memory_limit=CONTAINER_ADMIN_MEMORY_LIMIT,
                min_scale=CONTAINER_ADMIN_MIN_SCALE,
                max_scale=CONTAINER_ADMIN_MAX_SCALE,
                privacy=cnt.ContainerPrivacy.PRIVATE,
                protocol=cnt.ContainerProtocol.HTTP1,
                http_option=cnt.ContainerHttpOption.REDIRECTED,
                registry_image=IMAGE_TAG,
                environment_variables=admin_container_env_vars,
                secret_environment_variables=secret_env_vars,
            )

            click.secho(f"Deploying container {CONTAINER_ADMIN_NAME}")

            self.containers.deploy_container(container_id=created_container.id)

        container = self._get_container()
        if container is not None:
            click.secho(f"Container {CONTAINER_NAME} already exists")
        else:
            click.secho(f"Creating container {CONTAINER_NAME}")

            created_container = self.containers.create_container(
                namespace_id=namespace.id,
                name=CONTAINER_NAME,
                memory_limit=CONTAINER_MEMORY_LIMIT,
                min_scale=CONTAINER_MIN_SCALE,
                max_scale=CONTAINER_MAX_SCALE,
                privacy=cnt.ContainerPrivacy.PUBLIC,
                protocol=cnt.ContainerProtocol.HTTP1,
                http_option=cnt.ContainerHttpOption.REDIRECTED,
                registry_image=IMAGE_TAG,
                environment_variables=container_env_vars,
                secret_environment_variables=secret_env_vars,
            )

            click.secho(f"Deploying container {CONTAINER_NAME}")
            self.containers.deploy_container(container_id=created_container.id)

    def delete_containers(self):
        admin_container = self._get_admin_container()
        container = self._get_container()

        if admin_container:
            click.secho(f"Deleting container {CONTAINER_ADMIN_NAME}")
            self.containers.delete_container(container_id=admin_container.id)

        if container:
            click.secho(f"Deleting container {CONTAINER_NAME}")
            self.containers.delete_container(container_id=container.id)

    def check_containers(self):
        admin_container = self._get_admin_container_or_abort()
        container = self._get_container_or_abort()

        click.secho(f"Admin container status: {admin_container.status}")
        click.secho(f"Container status: {container.status}")

    def await_containers(self):
        admin_container = self._get_admin_container_or_abort()
        container = self._get_container_or_abort()

        # Execute in parallel
        results = futures.ThreadPoolExecutor(max_workers=2).map(
            self.containers.wait_for_container, [admin_container.id, container.id]
        )
        for res in results:
            if res.status == cnt.ContainerStatus.ERROR:
                click.secho(
                    f"Container {res.name} is in error: {res.error_message}"
                    "Check the logs for more details.",
                    fg="red",
                    bold=True,
                )
                raise click.Abort()
            if res.status != cnt.ContainerStatus.READY:
                click.secho(f"Container {res.name} is not ready", fg="red", bold=True)
                raise click.Abort()

        click.secho("Containers ready", fg="green", bold=True)

    def create_admin_container_token(self) -> str:
        admin_container = self._get_admin_container_or_abort()
        token = self.containers.create_token(container_id=admin_container.id)
        return token.token

    def update_container(self, db_password: str):
        self.update_container_without_deploy(db_password=db_password)

        admin_container = self._get_admin_container_or_abort()
        container = self._get_container_or_abort()

        click.secho("Deploying admin container...")
        self.containers.deploy_container(container_id=admin_container.id)

        click.secho("Deploying container...")
        self.containers.deploy_container(container_id=container.id)

    def update_container_without_deploy(self, db_password: str):
        admin_container = self._get_admin_container_or_abort()
        container = self._get_container_or_abort()

        container_admin_env_vars, container_env_vars = self._get_container_env_vars()
        secret_env_vars = self._get_container_secret_env_vars(db_password)

        click.secho("Updating admin container")

        self.containers.update_container(
            container_id=admin_container.id,
            privacy=cnt.ContainerPrivacy.PRIVATE,
            memory_limit=CONTAINER_ADMIN_MEMORY_LIMIT,
            min_scale=CONTAINER_ADMIN_MIN_SCALE,
            max_scale=CONTAINER_ADMIN_MAX_SCALE,
            protocol=cnt.ContainerProtocol.HTTP1,
            http_option=cnt.ContainerHttpOption.REDIRECTED,
            registry_image=IMAGE_TAG,
            environment_variables=container_admin_env_vars,
            secret_environment_variables=secret_env_vars,
        )

        click.secho("Updating container")

        self.containers.update_container(
            container_id=container.id,
            privacy=cnt.ContainerPrivacy.PRIVATE,
            memory_limit=CONTAINER_MEMORY_LIMIT,
            min_scale=CONTAINER_MIN_SCALE,
            max_scale=CONTAINER_MAX_SCALE,
            protocol=cnt.ContainerProtocol.HTTP1,
            http_option=cnt.ContainerHttpOption.REDIRECTED,
            registry_image=IMAGE_TAG,
            environment_variables=container_env_vars,
            secret_environment_variables=secret_env_vars,
        )

    def set_custom_domain(self):
        raise NotImplementedError
