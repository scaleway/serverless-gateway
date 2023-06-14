import click

from cli import client
from cli.gateway import GatewayManager
from cli.infra import InfraManager, cockpit
from cli.model import Route

DB_PASSWORD_OPTION = click.option(
    "--db-password",
    required=False,
    help="The password to use for the database. Will be generated if not provided.",
    envvar="DB_PASSWORD",
)
NO_METRICS_OPTION = click.option(
    "--no-metrics",
    is_flag=True,
    default=False,
    help="Disable Kong metrics integration with Cockpit.",
)


@click.group()
def cli():
    """CLI for managing the gateway.

    See the README for more information.
    """


@cli.command()
def local_config():
    """Sets up config for local deployment"""
    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)
    manager.set_up_config(True)


@cli.command()
def remote_config():
    """Sets up config for remote deployment"""
    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)
    manager.set_up_config(False)


@cli.command()
def get_routes():
    """Returns the routes configured on the gateway"""
    manager = GatewayManager()
    manager.print_routes()


@cli.command()
@click.argument("relative_url")
@click.argument("target")
@click.option(
    "--cors", is_flag=True, default=False, help="Add permissive cors to the route."
)
def add_route(relative_url, target, cors):
    """Adds a route to the gateway"""
    manager = GatewayManager()

    route = Route(relative_url, target, cors=cors)
    manager.add_route(route)


@cli.command()
@click.argument("relative_url")
@click.argument("target")
def delete_route(relative_url, target):
    """Deletes a route from the gateway"""
    manager = GatewayManager()

    route = Route(relative_url, target)
    manager.delete_route(route)


# TODO: integrate with existing CLI commands
@cli.command()
def setup_metrics():
    """Adds metrics plugin to the gateway"""
    gateway = GatewayManager()
    gateway.setup_global_kong_statsd_plugin()


@cli.command()
def create_admin_token():
    """Creates a token for the admin container"""
    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)
    token = manager.create_admin_container_token()
    click.secho(token)


@cli.command()
def delete_containers():
    """Deletes the containers used for the gateway"""
    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)
    manager.delete_containers()


@cli.command()
def get_endpoint():
    """Returns the endpoint for the gateway"""
    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)
    endpoint = manager.get_gateway_endpoint()
    click.secho(endpoint)


@cli.command()
def get_admin_endpoint():
    """Returns the endpoint for the gateway admin"""
    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)
    endpoint = manager.get_gateway_admin_endpoint()
    click.secho(endpoint)


@cli.command()
@DB_PASSWORD_OPTION
@click.option(
    "--no-save", is_flag=True, default=False, help="Do not save the password."
)
def create_db(db_password: str | None, no_save: bool):
    """Creates the database for the gateway.

    If --no-save is passed, the password will not be saved to Secret Manager.
    The password will therefore need to be provided for other commands.
    """
    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)
    manager.create_db(password=db_password, save_password=not no_save)


@cli.command()
def delete_db():
    """Deletes the database for the gateway."""
    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)
    manager.delete_db()


@cli.command()
def check_db():
    """Checks the status of the database"""
    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)
    manager.check_db()


@cli.command()
def await_db():
    """Waits for the database to be ready"""
    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)
    manager.await_db()


@cli.command()
def create_namespace():
    """Creates the container container namespace"""
    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)
    manager.create_namespace()


@cli.command()
def check_namespace():
    """Checks the status of the container namespace"""
    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)
    manager.check_namespace()


@cli.command()
def await_namespace():
    """Waits for the namespace to be ready"""
    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)
    manager.await_namespace()


@cli.command()
def delete_namespace():
    """Deletes the container namespace"""
    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)
    manager.delete_namespace()


@cli.command()
@DB_PASSWORD_OPTION
@NO_METRICS_OPTION
def create_containers(db_password: str | None, no_metrics: bool):
    """Creates the containers"""
    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)
    if not no_metrics:
        # Check that Cockpit is activated
        no_metrics = not cockpit.ensure_cockpit_activated(scw_client=scw_client)
    manager.create_containers(db_password=db_password, forward_metrics=not no_metrics)


@cli.command()
def check_containers():
    """Checks the status of the containers"""
    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)
    manager.check_containers()


@cli.command()
def await_containers():
    """Waits for the containers to be ready"""
    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)
    manager.await_containers()


@cli.command()
def set_custom_domain():
    """Sets the custom domain for the gateway container"""
    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)
    manager.set_custom_domain()


@cli.command()
@click.option(
    "--no-redeploy",
    is_flag=True,
    default=False,
    help="Don't redeploy the container, just update.",
)
@DB_PASSWORD_OPTION
def update_containers(
    no_redeploy: bool,
    db_password: str | None,
):
    """Updates the containers"""
    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)

    if no_redeploy:
        manager.update_container_without_deploy(db_password=db_password)
    else:
        manager.update_container(db_password=db_password)
