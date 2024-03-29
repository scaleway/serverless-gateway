import typing as t

import click
import scaleway.rdb.v1 as rdb
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn

from cli import client, conf
from cli.commands import options
from cli.commands.human import progress
from cli.console import console
from cli.gateway import GatewayManager
from cli.infra import InfraManager


@click.group()
def infra():
    """Set up the components to run the gateway\n
    https://serverless-gateway.readthedocs.io/en/latest/architecture.html"""


@infra.command()
@options.profile_option
def deploy(profile: t.Optional[str]):
    """Deploy all the gateway components"""

    scw_client = client.get_scaleway_client(profile_name=profile)
    manager = InfraManager(scw_client)

    progress_columns = progress.get_ultraviolet_styled_progress_columns()

    instance = manager.create_db()
    # This avoids showing the progress bar if the instance is already running
    if instance.status in rdb.INSTANCE_TRANSIENT_STATUSES:
        with Progress(
            SpinnerColumn(style=progress.ULTRAVIOLET_GREEN_STYLE),
            *progress_columns,
            TimeElapsedColumn(),
            console=console,
            transient=False,
        ) as progres_bar:
            manager.await_db(
                on_tick=progress.database_deployment_progress_cb(progres_bar)
            )

    manager.ensure_cockpit_activated()

    with console.status(
        "Creating Kong container namespace",
        spinner_style=progress.ULTRAVIOLET_GREEN_STYLE,
    ):
        manager.create_namespace()
        manager.await_namespace()

    with console.status(
        "Deploying Kong containers",
        spinner_style=progress.ULTRAVIOLET_GREEN_STYLE,
    ):
        manager.create_containers()
        manager.await_containers()

    console.print("Setting up local configuration file")
    manager.set_up_config(False)

    console.print("Enabling metrics")
    gateway = GatewayManager()
    gateway.setup_global_kong_statsd_plugin()

    console.print("Setting up Grafana")
    manager.import_kong_dashboard()

    manager.print_summary()


@infra.command()
@options.profile_option
def summary(profile: t.Optional[str] = None):
    """Print a summary of the gateway components"""
    scw_client = client.get_scaleway_client(profile_name=profile)
    manager = InfraManager(scw_client)

    manager.print_summary()


@infra.command()
@options.profile_option
def check(profile: t.Optional[str] = None):
    """Check the status of all gateway components"""
    scw_client = client.get_scaleway_client(profile_name=profile)
    manager = InfraManager(scw_client)

    manager.check_db()
    manager.check_namespace()
    manager.check_containers()


@infra.command()
@options.not_interactive_option
@options.profile_option
def delete(yes: bool, profile: t.Optional[str] = None):
    """Delete all the gateway components"""

    do_delete = yes
    if not do_delete:
        do_delete = click.confirm(
            "This will delete all the components of your gateway. Are you sure?"
        )

    if not do_delete:
        return

    scw_client = client.get_scaleway_client(profile_name=profile)
    manager = InfraManager(scw_client)

    manager.delete_containers()
    manager.delete_db()
    manager.delete_namespace()


@infra.command()
@options.profile_option
def config(profile: t.Optional[str]):
    """Set up the gateway config file"""
    scw_client = client.get_scaleway_client(profile_name=profile)
    manager = InfraManager(scw_client)
    manager.set_up_config(False)


@infra.command()
@options.profile_option
def endpoint(profile: t.Optional[str]):
    """Print the endpoint for the gateway"""
    scw_client = client.get_scaleway_client(profile_name=profile)
    manager = InfraManager(scw_client)
    gateway_endpoint = manager.get_gateway_endpoint()
    console.print(gateway_endpoint)


@infra.command()
@options.profile_option
def ip(profile: t.Optional[str]):  # pylint: disable=invalid-name
    """Print the IP for the gateway"""
    scw_client = client.get_scaleway_client(profile_name=profile)
    manager = InfraManager(scw_client)
    gateway_ip = manager.get_gateway_ip()
    console.print(gateway_ip)


@infra.command()
@options.profile_option
def admin_endpoint(profile: t.Optional[str]):
    """Print the endpoint for the gateway admin"""
    scw_client = client.get_scaleway_client(profile_name=profile)
    manager = InfraManager(scw_client)
    gateway_admin_endpoint = manager.get_gateway_admin_endpoint()
    console.print(gateway_admin_endpoint)


@infra.command()
@options.profile_option
def admin_token(profile: t.Optional[str]):
    """Print the token for accessing the admin container"""
    infra_conf = conf.InfraConfiguration.load()

    # WARNING: must use raw print here to avoid line-breaks
    print(infra_conf.gw_admin_token)


@infra.command()
@options.profile_option
def new_admin_token(profile: t.Optional[str]):
    """Create a new token for the admin container"""
    scw_client = client.get_scaleway_client(profile_name=profile)
    manager = InfraManager(scw_client)
    token = manager.create_admin_container_token()

    # WARNING: must use raw print here to avoid line-breaks
    print(token)
