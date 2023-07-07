import click
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn

from cli import client, conf
from cli.gateway import GatewayManager
from cli.infra import InfraManager
from cli.console import console
from cli.commands.human import progress


@click.group()
def infra():
    """Manage gateway infrastructure"""
    pass


@infra.command()
def deploy():
    """Deploy all the gateway components"""

    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)

    progress_columns = progress.get_ultraviolet_styled_progress_columns()

    with Progress(
        SpinnerColumn(),
        *progress_columns,
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as p:
        manager.create_db()
        manager.await_db(on_tick=progress.database_deployment_progress_cb(p))

    console.print("Checking cockpit activated", style="blue")
    manager.ensure_cockpit_activated()

    with console.status("Creating container namespace"):
        manager.create_namespace()
        manager.await_namespace()

    with Progress(
        SpinnerColumn(),
        *progress_columns,
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as p:
        manager.create_containers()
        manager.await_containers(
            on_gateway_tick=progress.container_deployment_progress_cb(
                p, container_name="gateway"
            ),
            on_admin_tick=progress.container_deployment_progress_cb(
                p, container_name="admin"
            ),
        )

    console.print("Setting up configuration", style="blue")
    manager.set_up_config(False)

    console.print("Enabling metrics", style="blue")
    gateway = GatewayManager()
    gateway.setup_global_kong_statsd_plugin()

    click.secho("Setting up Grafana", fg="blue")
    manager.import_kong_dashboard()


@infra.command()
def check():
    """Check the status of all gateway components"""
    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)

    manager.check_db()
    manager.check_namespace()
    manager.check_containers()


@infra.command()
@click.option(
    "--yes", "-y", is_flag=True, default=False, help="Skip interactive confirmation"
)
def delete(yes):
    """Delete all the gateway components"""

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


@infra.command()
def config():
    """Set up the gateway config file"""
    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)
    manager.set_up_config(False)


@infra.command()
def endpoint():
    """Print the endpoint for the gateway"""
    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)
    endpoint = manager.get_gateway_endpoint()
    click.secho(endpoint)


@infra.command()
def ip():
    """Print the IP for the gateway"""
    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)
    endpoint = manager.get_gateway_ip()
    click.secho(endpoint)


@infra.command()
def admin_endpoint():
    """Print the endpoint for the gateway admin"""
    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)
    endpoint = manager.get_gateway_admin_endpoint()
    click.secho(endpoint)


@infra.command()
def admin_token():
    """Print the token for accessing the admin container"""
    c = conf.InfraConfiguration.load()
    click.secho(c.gw_admin_token)


@infra.command()
def new_admin_token():
    """Create a new token for the admin container"""
    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)
    token = manager.create_admin_container_token()
    click.secho(token)
