import sys

import click
from loguru import logger

from cli import client, conf
from cli.gateway import GatewayManager
from cli.infra import InfraManager, cockpit
from cli.model import Route


@click.group()
def cli():
    """CLI for managing the gateway.

    See the README for more information.
    """
    # Set log level
    logger.remove()
    logger.add(sys.stderr, level="INFO")


@cli.command()
def deploy():
    """Deploys all the gateway components"""

    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)

    click.secho("Creating database", fg="blue")
    manager.create_db()
    manager.await_db()

    click.secho("Creating container namespace", fg="blue")
    manager.create_namespace()
    manager.await_namespace()

    click.secho("Checking cockpit activated", fg="blue")
    cockpit.ensure_cockpit_activated(scw_client=scw_client)

    click.secho("Creating containers", fg="blue")
    manager.create_containers()
    manager.await_containers()

    click.secho("Setting up configuration", fg="blue")
    manager.set_up_config(False)

    click.secho("Enabling metrics", fg="blue")
    gateway = GatewayManager()
    gateway.setup_global_kong_statsd_plugin()


@cli.command()
def check():
    """Checks the status of all gateway components"""
    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)

    manager.check_db()
    manager.check_namespace()
    manager.check_containers()


@cli.command()
@click.option(
    "--yes", "-y", is_flag=True, default=False, help="Skip interactive confirmation"
)
def delete(yes):
    """Deletes all the gateway components"""

    do_delete = yes
    if not do_delete:
        do_delete = click.confirm(
            "This will delete all the components of your gateway. Are you sure?"
        )

    if do_delete:
        scw_client = client.get_scaleway_client()
        manager = InfraManager(scw_client)

        manager.delete_containers()
        manager.delete_db()
        manager.delete_namespace()


@cli.command()
def dev_config():
    """Sets up config for local development"""
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
    """Prints the routes configured on the gateway"""
    manager = GatewayManager()
    manager.print_routes()


@cli.command()
@click.argument("relative_url")
@click.argument("target")
@click.option(
    "--cors", is_flag=True, default=False, help="Add permissive cors to the route."
)
@click.option("--jwt", is_flag=True, default=False, help="Add JWT auth to the route.")
@click.option(
    "--http-methods",
    "-m",
    help="HTTP methods that the route should accept. Defaults to all if not specified.",
    multiple=True,
)
def add_route(
    relative_url: str, target: str, cors: bool, jwt: bool, http_methods: list[str]
):
    """Adds a route to the gateway"""
    manager = GatewayManager()

    route = Route(
        relative_url=relative_url,
        target=target,
        cors=cors,
        jwt=jwt,
        http_methods=http_methods,
    )
    manager.add_route(route)


@cli.command()
@click.argument("relative_url")
@click.argument("target")
def delete_route(relative_url, target):
    """Deletes a route from the gateway"""
    manager = GatewayManager()

    route = Route(relative_url, target)
    manager.delete_route(route)


@cli.command()
def get_consumers():
    """Prints the consumers configured on the gateway"""
    manager = GatewayManager()
    manager.print_consumers()


@cli.command()
@click.argument("name")
def add_consumer(name):
    """Adds a consumer to the gateway"""
    manager = GatewayManager()
    manager.add_consumer(name)


@cli.command()
@click.argument("name")
def delete_consumer(name):
    """Deletes a consumer from the gateway"""
    manager = GatewayManager()
    manager.delete_consumer(name)


@cli.command()
@click.argument("consumer")
def add_jwt_cred(consumer):
    """Adds a JWT credential to a consumer"""
    manager = GatewayManager()
    cred = manager.add_jwt_cred(consumer)
    manager.print_jwt_cred(cred)


@cli.command()
@click.argument("consumer")
def get_jwt_creds(consumer):
    """Lists the JWT credentials for a consumer"""
    manager = GatewayManager()
    manager.print_jwt_creds(consumer)


@cli.command()
def create_admin_token():
    """Creates a new token for the admin container"""
    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)
    token = manager.create_admin_container_token()
    click.secho(token)


@cli.command()
def get_endpoint():
    """Prints the endpoint for the gateway"""
    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)
    endpoint = manager.get_gateway_endpoint()
    click.secho(endpoint)


@cli.command()
def get_admin_endpoint():
    """Prints the endpoint for the gateway admin"""
    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)
    endpoint = manager.get_gateway_admin_endpoint()
    click.secho(endpoint)


@cli.command()
def get_admin_token():
    """Prints the token for accessing the admin container"""
    c = conf.InfraConfiguration.load()
    click.secho(c.gw_admin_token)


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
def update_containers(
    no_redeploy: bool,
):
    """Updates the containers"""
    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)

    if no_redeploy:
        manager.update_container_without_deploy()
    else:
        manager.update_container()
