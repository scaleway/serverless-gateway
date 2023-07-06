import click

from cli import client
from cli.infra import InfraManager


@click.group()
def domain():
    """Manage gateway domains"""
    pass


@domain.command()
def ls():
    """Print the domains configured on the gateway"""
    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)
    manager.print_domains_for_container()


@domain.command()
@click.argument("domain")
def add(domain):
    """Add a domain to the gateway"""
    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)
    manager.add_custom_domain(domain)


@domain.command()
@click.argument("domain")
def delete(domain):
    """Remove a domain from the gateway"""
    scw_client = client.get_scaleway_client()
    manager = InfraManager(scw_client)
    manager.delete_custom_domain(domain)
