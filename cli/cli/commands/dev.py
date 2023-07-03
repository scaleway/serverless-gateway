import click

from cli import client
from cli.infra import InfraManager


@click.group()
def dev():
    """Develop locally"""
    pass


@dev.command()
def config():
    """Set up config for local development"""
    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)
    manager.set_up_config(True)


@dev.command()
@click.option(
    "--no-redeploy",
    is_flag=True,
    default=False,
    help="Don't redeploy the container, just update.",
)
def update_containers(
    no_redeploy: bool,
):
    """Update the containers"""
    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)

    if no_redeploy:
        manager.update_container_without_deploy()
    else:
        manager.update_container()
