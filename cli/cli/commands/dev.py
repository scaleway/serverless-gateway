import typing as t

import click

from cli import client
from cli.commands import options
from cli.infra import InfraManager


@click.group()
def dev():
    """Develop the Gateway locally"""


@dev.command()
@options.profile_option
def config(profile: t.Optional[str]):
    """Set up config for local development"""
    scw_client = client.get_scaleway_client(profile_name=profile)
    manager = InfraManager(scw_client)
    manager.set_up_config(True)


@dev.command()
@click.option(
    "--no-redeploy",
    is_flag=True,
    default=False,
    help="Don't redeploy the container, just update.",
)
@options.profile_option
def update_containers(
    no_redeploy: bool,
    profile: t.Optional[str],
):
    """Update the containers"""
    scw_client = client.get_scaleway_client(profile_name=profile)
    manager = InfraManager(scw_client)

    if no_redeploy:
        manager.update_container_without_deploy()
    else:
        manager.update_container()
