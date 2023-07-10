import socket
import typing as t
from concurrent import futures

import click
import scaleway.cockpit.v1beta1 as cpt
import scaleway.container.v1beta1 as cnt
import scaleway.function.v1beta1 as fnc
import scaleway.rdb.v1 as rdb
import scaleway.secret.v1alpha1 as sec
from loguru import logger
from rich.table import Table
from scaleway import Client, ScalewayException
from scaleway_core.utils import WaitForOptions

from cli import conf, infra

from ..console import console


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
            console.print(
                f"Namespace {namespace_name} not found",
                style="bold red",
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
            console.print(
                f"{container_name} container not found.",
                style="bold red",
            )
            raise click.Abort()

        return container

    def _get_admin_container_or_abort(self) -> cnt.Container:
        return self._get_container_or_abort(admin=True)

    def _get_database_instance_or_abort(self) -> rdb.Instance:
        instance_name = infra.rdb.DB_INSTANCE_NAME
        instance = infra.rdb.get_database_instance_by_name(self.rdb, instance_name)
        if not instance:
            console.print(
                f"Database instance {instance_name} not found",
                style="bold red",
            )
            raise click.Abort()
        if instance.status == rdb.InstanceStatus.DELETING:
            raise click.Abort()

        return instance

    def _get_database_endpoint_or_abort(
        self, database_instance: rdb.Instance
    ) -> tuple[str, int]:
        endpoints = database_instance.endpoints
        if not endpoints:
            console.print(
                f"Database instance {database_instance.name} has no endpoints",
                style="bold red",
            )
            raise click.Abort()

        endpoint = endpoints[0]
        address = endpoint.ip or endpoint.hostname
        if not address:
            console.print(
                f"Database instance {database_instance.name} has no address",
                style="bold red",
            )
            raise click.Abort()

        return address, endpoint.port

    def _get_db_password_or_abort(self) -> str:
        try:
            password = infra.secrets.get_db_password(self.secrets)
            return password
        except ScalewayException as exception:
            if exception.status_code == 404:
                console.print(
                    "Database password not found in Secret Manager", style="red"
                )
                raise click.Abort()
            raise exception

    def get_gateway_endpoint(self) -> str:
        """Get the endpoint of the gateway."""
        container = self._get_container_or_abort()
        return container.domain_name

    def get_gateway_ip(self) -> str:
        """Get the IP of the gateway."""
        container = self._get_container_or_abort()
        ip = socket.gethostbyname(container.domain_name)
        return ip

    def get_gateway_admin_endpoint(self) -> str:
        """Get the endpoint of the gateway admin."""
        container = self._get_admin_container_or_abort()
        return container.domain_name

    def create_db(self) -> rdb.Instance:
        """Create the database instance."""

        instance_name = infra.rdb.DB_INSTANCE_NAME
        instance = infra.rdb.get_database_instance_by_name(self.rdb, instance_name)
        if instance:
            console.print(f"Database {instance_name} already exists")
            return instance

        console.print(f"Creating database instance {instance_name}...")

        logger.debug("Generating database password")
        password = infra.secrets.generate_database_password()

        logger.debug("Saving database password")
        infra.secrets.create_db_password_secret(self.secrets, password)

        instance = infra.rdb.create_database_instance(self.rdb, password)
        console.print("Database created", style="bold green")
        return instance

    def check_db(self):
        """Check the status of the database instance."""
        instance = self._get_database_instance_or_abort()
        console.print(f"Database status: {instance.status}", style="bold")

    def await_db(self, on_tick: t.Callable[[rdb.Instance], None]) -> None:
        """Wait for the database instance to be ready."""
        instance = self._get_database_instance_or_abort()
        if instance.status == rdb.InstanceStatus.READY:
            return

        options: WaitForOptions[rdb.Instance, bool] = WaitForOptions()
        options.stop = lambda instance: on_tick(instance) or (
            instance.status not in rdb.INSTANCE_TRANSIENT_STATUSES
        )
        instance = self.rdb.wait_for_instance(
            instance_id=instance.id,
            options=options,
        )

        if instance.status != rdb.InstanceStatus.READY:
            console.print("Database is not ready", style="bold red")
            raise click.Abort()

    def delete_db(self) -> None:
        """Delete the database instance."""
        # Delete the secret
        infra.secrets.delete_db_password_secret(self.secrets)

        # Delete the database
        instance = self._get_database_instance_or_abort()
        self.rdb.delete_instance(instance_id=instance.id)
        console.print("Database deleted")

    def create_namespace(self):
        """Create the namespace for the gateway."""
        namespace_name = infra.cnt.CONTAINER_NAMESPACE
        namespace = infra.cnt.get_namespace_by_name(self.containers, namespace_name)

        if namespace:
            console.print("Namespace already exists")
            return

        infra.cnt.create_namespace(self.containers)

    def check_namespace(self):
        """Check the status of the namespace."""
        namespace = self._get_namespace_or_abort()
        if namespace.status == cnt.NamespaceStatus.ERROR:
            console.print(
                f"Namespace in error: {namespace.error_message}",
                style="bold red",
            )
            raise click.Abort()

        console.print(f"Namespace status: {namespace.status}", style="bold")

    def await_namespace(self):
        """Wait for the namespace to be ready."""

        console.print("Waiting for namespace to be ready...", style="blue")

        namespace = self._get_namespace_or_abort()
        namespace = self.containers.wait_for_namespace(namespace_id=namespace.id)
        if namespace.status == cnt.NamespaceStatus.ERROR:
            console.print(
                f"Namespace in error: {namespace.error_message}",
                style="bold red",
            )
            raise click.Abort()

        if namespace.status != cnt.NamespaceStatus.READY:
            console.print("Namespace is not ready", style="bold red")
            raise click.Abort()

        console.print("Namespace ready")

    def delete_namespace(self):
        """Delete the namespace."""
        namespace = self._get_namespace_or_abort()
        self.containers.delete_namespace(namespace_id=namespace.id)
        console.print("Namespace deleted")

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
            console.print(
                f"Admin container {admin_container_name} already exists",
            )
        else:
            console.print(
                f"Creating admin container {admin_container_name}",
            )
            created_container = infra.cnt.create_kong_admin_container(
                self.containers, namespace.id, db_host, db_port, db_password
            )
            console.print(f"Deploying container {admin_container_name}")
            self.containers.deploy_container(container_id=created_container.id)

        container_name = infra.cnt.CONTAINER_NAME
        container = infra.cnt.get_container_by_name(
            self.containers, namespace.id, container_name
        )
        if container:
            console.print(f"Container {container_name} already exists")
            return

        console.print(
            f"Creating container {container_name} from tag {infra.image.IMAGE_TAG}"
        )

        # Check if token exists
        token = infra.cpt.get_metrics_token(self.cockpit)
        if token:
            console.print("Cockpit token already exists, deleting")
            infra.cpt.delete_metrics_token(self.cockpit, token)

        console.print("Creating Cockpit token")
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

        console.print(f"Deploying container {container_name}")
        self.containers.deploy_container(container_id=created_container.id)

    def check_containers(self):
        """Check the status of the containers."""
        admin_container = self._get_admin_container_or_abort()
        container = self._get_container_or_abort()

        console.print(f"Admin container status: {admin_container.status}", style="bold")
        console.print(f"Container status: {container.status}", style="bold")

    def _handle_container_not_ready(self, container: cnt.Container) -> None:
        """Handle a container that is not ready."""
        if container.status == cnt.ContainerStatus.ERROR:
            console.print(
                f"Container {container.name} is in error: {container.error_message}",
                style="bold red",
            )
            raise click.Abort()

        if container.status != cnt.ContainerStatus.READY:
            console.print(f"Container {container.name} is not ready", style="bold red")
            raise click.Abort()

    def await_containers(self):
        """Wait for the containers to be ready."""

        console.print("Waiting for containers to be ready...", style="blue")

        admin_container = self._get_admin_container_or_abort()
        container = self._get_container_or_abort()

        # Execute in parallel
        executor = futures.ThreadPoolExecutor(max_workers=2)
        admin_future = executor.submit(
            lambda id: self.containers.wait_for_container(container_id=id),
            admin_container.id,
        )
        container_future = executor.submit(
            lambda id: self.containers.wait_for_container(container_id=id),
            container.id,
        )

        # Wait for both futures to complete
        futures.wait(
            [admin_future, container_future], return_when=futures.ALL_COMPLETED
        )

        admin_container = admin_future.result()
        self._handle_container_not_ready(admin_container)

        container = container_future.result()
        self._handle_container_not_ready(container)

        console.print("Containers are ready")

    def delete_containers(self):
        """Delete the containers."""
        admin_container = self._get_admin_container_or_abort()
        container = self._get_container_or_abort()

        self.containers.delete_container(container_id=admin_container.id)
        console.print("Admin container deleted")

        self.containers.delete_container(container_id=container.id)
        console.print("Gateway container deleted")

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

        console.print("Deploying admin container...")
        self.containers.deploy_container(container_id=admin_container.id)

        console.print("Deploying container...")
        self.containers.deploy_container(container_id=container.id)

    def update_container_without_deploy(self):
        """Update the container without deploying it."""
        admin_container = self._get_admin_container_or_abort()
        container = self._get_container_or_abort()

        database_instance = self._get_database_instance_or_abort()
        db_host, db_port = self._get_database_endpoint_or_abort(database_instance)
        db_password = self._get_db_password_or_abort()

        console.print(f"Updating container {admin_container.name}")
        infra.cnt.update_kong_admin_container(
            self.containers, admin_container.id, db_host, db_port, db_password
        )
        console.print(f"Updating container {container.name}")

        token, metrics_push_url = None, None
        if container.environment_variables.get("FORWARD_METRICS"):
            token = infra.cpt.get_metrics_token(self.cockpit)
            if token:
                infra.cpt.delete_metrics_token(self.cockpit, token)

            console.print("Creating Cockpit token to forward metrics...")
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

    def print_domains_for_container(self) -> None:
        """Prints the custom domains set on the container"""
        container = self._get_container_or_abort()
        domains = self.containers.list_domains_all(container_id=container.id)

        table = Table("HOSTNAME", "URL", "STATUS", title="Domains")
        for domain in domains:
            table.add_row(domain.hostname, domain.url, domain.status)
        console.print(table)

    def _get_domain(self, container_id: str, domain_host: str):
        domains = self.containers.list_domains_all(container_id=container_id)
        for d in domains:
            if d.hostname == domain_host:
                return d

        return None

    def add_custom_domain(self, domain_host: str):
        """Set a custom domain for the container."""
        container = self._get_container_or_abort()

        existing = self._get_domain(container.id, domain_host)
        if existing:
            click.echo("Container domain already exists, deleting")
            self.containers.delete_domain(domain_id=existing.id)

        click.echo(f"Adding domain {domain_host}")
        self.containers.create_domain(hostname=domain_host, container_id=container.id)

    def await_custom_domain(self, domain_host: str) -> None:
        """Wait for the custom domain to be ready."""
        container = self._get_container_or_abort()

        console.log(f"Waiting for domain {domain_host} to be ready...", style="blue")

        domain = self._get_domain(container.id, domain_host)
        domain_waited = self.containers.wait_for_domain(domain_id=domain.id)

        if domain_waited.status != cnt.DomainStatus.READY:
            console.print("Domain is not ready", style="bold red")
            raise click.Abort()

        console.print("Domain ready")

    def delete_custom_domain(self, domain_host: str):
        """Delete a custom domain for the container."""
        container = self._get_container_or_abort()

        domain = self._get_domain(container.id, domain_host)
        if domain:
            click.echo(f"Deleting domain {domain}")
            self.containers.delete_domain(domain_id=domain.id)
        else:
            click.echo(f"Domain {domain} already deleted")

    def ensure_cockpit_activated(self):
        """Check if the cockpit is activated."""
        infra.cpt.ensure_cockpit_activated(self.cockpit)

    def import_kong_dashboard(self):
        """Import the kong dashboard via the Grafana API."""
        # We need to create a temporary user to import the dashboard
        with infra.cpt.temporary_grafana_user(api=self.cockpit) as user:
            url = infra.cpt.import_kong_statsd_dashboard(api=self.cockpit, user=user)
            click.secho(f"Kong dashboard available at:\n {url}", fg="green")
