import typing as t

import click

from cli import client
from cli.commands import options
from cli.infra import InfraManager


@click.group()
def domain():
    """Add alternative URLs for the gateway\n
    https://serverless-gateway.readthedocs.io/en/latest/domains.html"""


@domain.command()
@options.profile_option
def ls(profile: t.Optional[str]):  # pylint: disable=invalid-name
    """Print the domains configured on the gateway"""
    scw_client = client.get_scaleway_client(profile_name=profile)
    manager = InfraManager(scw_client)
    manager.print_domains_for_container()


@domain.command()
@options.profile_option
@click.argument("domain", type=str)
def add(domain: str, profile: t.Optional[str]):  # pylint: disable=redefined-outer-name
    """Add a domain to the gateway"""
    scw_client = client.get_scaleway_client(profile_name=profile)
    manager = InfraManager(scw_client)
    manager.add_custom_domain(domain)


@domain.command()
@click.argument("domain", type=str)
def delete(
    domain: str, profile: t.Optional[str]
):  # pylint: disable=redefined-outer-name
    """Remove a domain from the gateway"""
    scw_client = client.get_scaleway_client(profile_name=profile)
    manager = InfraManager(scw_client)
    manager.delete_custom_domain(domain)
