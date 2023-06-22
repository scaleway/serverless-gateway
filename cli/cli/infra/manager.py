from concurrent import futures

import click
import scaleway.cockpit.v1beta1 as cpt
import scaleway.container.v1beta1 as cnt
import scaleway.function.v1beta1 as fnc
import scaleway.rdb.v1 as rdb
import scaleway.secret.v1alpha1 as sec
from loguru import logger
from scaleway import Client, ScalewayException

from cli import conf, infra


class InfraManager:
    """Manager for the infrastructure of the gateway.

    .. note::
        This class is used by the CLI to manage the infrastructure of the gateway.

        References:
            `Scaleway API documentation`_
            `Scaleway Python SDK`_

        .. _Scaleway API documentation:_ https://www.scaleway.com/en/developers/api/
        .. _Scaleway Python SDK:_ https://github.com/scaleway/scaleway-sdk-python
    """

    def __init__(self, scw_client: Client):
        # Initialise SCW client
        self.scw_client = scw_client

        # Init Scaleway APIs
        self.containers = cnt.ContainerV1Beta1API(
            self.scw_client, bypass_validation=True
        )
        self.functions = fnc.FunctionV1Beta1API(self.scw_client, bypass_validation=True)
        self.rdb = rdb.RdbV1API(self.scw_client, bypass_validation=True)
        self.secrets = sec.SecretV1Alpha1API(self.scw_client, bypass_validation=True)
        self.cockpit = cpt.CockpitV1Beta1API(self.scw_client, bypass_validation=True)

    def set_up_config(self, is_local: bool) -> None:
        """Set up the configuration for the gateway.

        Used by the GatewayManager to set up the route configuration.
        """
        if is_local:
            config = conf.InfraConfiguration.from_local()
        else:
            config = conf.InfraConfiguration.from_infra(self)
        config.save()

    def _get_namespace_or_abort(self) -> cnt.Namespace:
        namespace_name = infra.cnt.CONTAINER_NAMESPACE
        namespace = infra.cnt.get_namespace_by_name(self.containers, namespace_name)
        if not namespace:
            click.secho(
                f"Namespace {namespace_name} not found",
                fg="red",
                bold=True,
            )
            raise click.Abort()

        return namespace

    def _get_container_or_abort(self, admin: bool = False) -> cnt.Container:
        namespace = self._get_namespace_or_abort()
        container_name = (
            infra.cnt.CONTAINER_ADMIN_NAME if admin else infra.cnt.CONTAINER_NAME
        )
        container = infra.cnt.get_container_by_name(
            self.containers, namespace.id, container_name
        )

        if not container:
            container_name = "Admin" if admin else "Gateway"
            click.secho(
                f"{container_name} container not found.",
                fg="red",
                bold=True,
            )
            raise click.Abort()

        return container

    def _get_admin_container_or_abort(self) -> cnt.Container:
        return self._get_container_or_abort(admin=True)

    def _get_database_instance_or_abort(self) -> rdb.Instance:
        instance_name = infra.rdb.DB_INSTANCE_NAME
        instance = infra.rdb.get_database_instance_by_name(self.rdb, instance_name)
        if not instance:
            click.secho(
                f"Database instance {instance_name} not found",
                fg="red",
                bold=True,
            )
            raise click.Abort()

        return instance

    def _get_database_endpoint_or_abort(
        self, database_instance: rdb.Instance
    ) -> tuple[str, int]:
        endpoints = database_instance.endpoints
        if not endpoints:
            click.secho(
                f"Database instance {database_instance.name} has no endpoints",
                fg="red",
                bold=True,
            )
            raise click.Abort()

        endpoint = endpoints[0]
        address = endpoint.ip or endpoint.hostname
        if not address:
            click.secho(
                f"Database instance {database_instance.name} has no address",
                fg="red",
                bold=True,
            )
            raise click.Abort()

        return address, endpoint.port

    def _get_db_password_or_abort(self) -> str:
        try:
            password = infra.secrets.get_db_password(self.secrets)
            return password
        except ScalewayException as exception:
            if exception.status_code == 404:
                click.secho("Database password not found in Secret Manager", fg="red")
                raise click.Abort()
            raise exception

    def get_gateway_endpoint(self) -> str:
        """Get the endpoint of the gateway."""
        container = self._get_container_or_abort()
        return container.domain_name

    def get_gateway_admin_endpoint(self) -> str:
        """Get the endpoint of the gateway admin."""
        container = self._get_admin_container_or_abort()
        return container.domain_name

    def create_db(self) -> None:
        """Create the database instance."""

        instance_name = infra.rdb.DB_INSTANCE_NAME
        instance = infra.rdb.get_database_instance_by_name(self.rdb, instance_name)
        if instance:
            click.secho(f"Database {instance_name} already exists")
            return

        click.secho(f"Creating database instance {instance_name}...")

        logger.debug("Generating database password")
        password = infra.secrets.generate_database_password()

        logger.debug("Saving database password")
        infra.secrets.create_db_password_secret(self.secrets, password)

        infra.rdb.create_database_instance(self.rdb, password)
        click.secho("Database created", fg="green", bold="true")

    def check_db(self):
        """Check the status of the database instance."""
        instance = self._get_database_instance_or_abort()
        click.secho(f"Database status: {instance.status}", bold=True)

    def await_db(self) -> None:
        """Wait for the database instance to be ready."""

        click.secho("Waiting for database to be ready...", fg="blue")

        instance = self._get_database_instance_or_abort()
        instance = self.rdb.wait_for_instance(instance_id=instance.id)

        if instance.status != rdb.InstanceStatus.READY:
            click.secho("Database is not ready", fg="red", bold="true")
            raise click.Abort()

        click.secho("Database ready")

    def delete_db(self) -> None:
        """Delete the database instance."""
        # Delete the secret
        infra.secrets.delete_db_password_secret(self.secrets)

        # Delete the database
        instance = self._get_database_instance_or_abort()
        self.rdb.delete_instance(instance_id=instance.id)
        click.secho("Database deleted")

    def create_namespace(self):
        """Create the namespace for the gateway."""
        namespace_name = infra.cnt.CONTAINER_NAMESPACE
        namespace = infra.cnt.get_namespace_by_name(self.containers, namespace_name)

        if namespace:
            click.secho("Namespace already exists")
            return

        click.secho(f"Creating namespace {namespace_name}...")
        infra.cnt.create_namespace(self.containers)

    def check_namespace(self):
        """Check the status of the namespace."""
        namespace = self._get_namespace_or_abort()
        if namespace.status == cnt.NamespaceStatus.ERROR:
            click.secho(
                f"Namespace in error: {namespace.error_message}",
                fg="red",
                bold="true",
            )
            raise click.Abort()

        click.secho(f"Namespace status: {namespace.status}", bold=True)

    def await_namespace(self):
        """Wait for the namespace to be ready."""

        click.secho("Waiting for namespace to be ready...", fg="blue")

        namespace = self._get_namespace_or_abort()
        namespace = self.containers.wait_for_namespace(namespace_id=namespace.id)
        if namespace.status == cnt.NamespaceStatus.ERROR:
            click.secho(
                f"Namespace in error: {namespace.error_message}",
                fg="red",
                bold=True,
            )
            raise click.Abort()

        if namespace.status != cnt.NamespaceStatus.READY:
            click.secho("Namespace is not ready", fg="red", bold=True)
            raise click.Abort()

        click.secho("Namespace ready")

    def delete_namespace(self):
        """Delete the namespace."""
        namespace = self._get_namespace_or_abort()
        self.containers.delete_namespace(namespace_id=namespace.id)
        click.secho("Namespace deleted")

    def create_containers(self) -> None:
        """Create containers for Kong and Kong Admin."""
        database_instance = self._get_database_instance_or_abort()
        db_password = self._get_db_password_or_abort()
        db_host, db_port = self._get_database_endpoint_or_abort(database_instance)

        # Namespace should be created before creating containers
        namespace = self._get_namespace_or_abort()

        admin_container_name = infra.cnt.CONTAINER_ADMIN_NAME
        admin_container = infra.cnt.get_container_by_name(
            self.containers, namespace.id, admin_container_name
        )
        if admin_container:
            click.secho(
                f"Admin container {admin_container_name} already exists",
            )
        else:
            click.secho(
                f"Creating admin container {admin_container_name}",
            )
            created_container = infra.cnt.create_kong_admin_container(
                self.containers, namespace.id, db_host, db_port, db_password
            )
            click.echo(f"Deploying container {admin_container_name}")
            self.containers.deploy_container(container_id=created_container.id)

        container_name = infra.cnt.CONTAINER_NAME
        container = infra.cnt.get_container_by_name(
            self.containers, namespace.id, container_name
        )
        if container:
            click.secho(f"Container {container_name} already exists")
            return

        click.secho(
            f"Creating container {container_name} from tag {infra.image.IMAGE_TAG}"
        )

        # Check if token exists
        token = infra.cpt.get_metrics_token(self.cockpit)
        if token:
            click.echo("Cockpit token already exists, deleting")
            infra.cpt.delete_metrics_token(self.cockpit, token)

        click.echo("Creating Cockpit token")
        token_key = infra.cpt.create_metrics_token(self.cockpit)
        metrics_push_url = infra.cpt.get_metrics_push_url(self.cockpit)

        created_container = infra.cnt.create_kong_container(
            self.containers,
            namespace.id,
            db_host,
            db_port,
            db_password,
            metrics_token=token_key,
            metrics_push_url=metrics_push_url,
        )

        click.secho(f"Deploying container {container_name}")
        self.containers.deploy_container(container_id=created_container.id)

    def check_containers(self):
        """Check the status of the containers."""
        admin_container = self._get_admin_container_or_abort()
        container = self._get_container_or_abort()

        click.secho(f"Admin container status: {admin_container.status}", bold=True)
        click.secho(f"Container status: {container.status}", bold=True)

    def await_containers(self):
        """Wait for the containers to be ready."""

        click.secho("Waiting for containers to be ready...", fg="blue")

        admin_container = self._get_admin_container_or_abort()
        container = self._get_container_or_abort()

        # Execute in parallel
        results = futures.ThreadPoolExecutor(max_workers=2).map(
            lambda id: self.containers.wait_for_container(container_id=id),
            (admin_container.id, container.id),
        )
        for res in results:
            if res.status == cnt.ContainerStatus.ERROR:
                click.secho(
                    f"Container {res.name} is in error: {res.error_message}"
                    ". Check the logs for more details.",
                    fg="red",
                    bold=True,
                )
                raise click.Abort()
            if res.status != cnt.ContainerStatus.READY:
                click.secho(f"Container {res.name} is not ready", fg="red", bold=True)
                raise click.Abort()
        click.secho("Containers are ready")

    def delete_containers(self):
        """Delete the containers."""
        admin_container = self._get_admin_container_or_abort()
        container = self._get_container_or_abort()

        self.containers.delete_container(container_id=admin_container.id)
        click.secho("Admin container deleted")

        self.containers.delete_container(container_id=container.id)
        click.secho("Gateway container deleted")

    def get_function_endpoint(
        self, namespace_name: str, function_name: str
    ) -> str | None:
        """Get the endpoint of a function."""
        return infra.fnc.get_function_endpoint_by_name(
            self.functions, namespace_name, function_name
        )

    def create_admin_container_token(self) -> str:
        """Create a token to access the private admin container."""
        admin_container = self._get_admin_container_or_abort()
        token = self.containers.create_token(container_id=admin_container.id)
        return token.token

    def update_container(self):
        """Update the container."""
        self.update_container_without_deploy()

        admin_container = self._get_admin_container_or_abort()
        container = self._get_container_or_abort()

        click.secho("Deploying admin container...")
        self.containers.deploy_container(container_id=admin_container.id)

        click.secho("Deploying container...")
        self.containers.deploy_container(container_id=container.id)

    def update_container_without_deploy(self):
        """Update the container without deploying it."""
        admin_container = self._get_admin_container_or_abort()
        container = self._get_container_or_abort()

        database_instance = self._get_database_instance_or_abort()
        db_host, db_port = self._get_database_endpoint_or_abort(database_instance)
        db_password = self._get_db_password_or_abort()

        click.echo(f"Updating container {admin_container.name}")
        infra.cnt.update_kong_admin_container(
            self.containers, admin_container.id, db_host, db_port, db_password
        )
        click.echo(f"Updating container {container.name}")

        token, metrics_push_url = None, None
        if container.environment_variables.get("FORWARD_METRICS"):
            token = infra.cpt.get_metrics_token(self.cockpit)
            if token:
                infra.cpt.delete_metrics_token(self.cockpit, token)

            click.echo("Creating Cockpit token to forward metrics...")
            token_key = infra.cpt.create_metrics_token(self.cockpit)
            metrics_push_url = infra.cpt.get_metrics_push_url(self.cockpit)

        infra.cnt.update_kong_container(
            self.containers,
            container.id,
            db_host,
            db_port,
            db_password,
            metrics_token=token_key,
            metrics_push_url=metrics_push_url,
        )

    def set_custom_domain(self):
        """Set a custom domain for the container."""
        raise NotImplementedError
