import click

from cli.gateway import GatewayManager


@click.group()
def consumer():
    """Manage gateway consumers"""
    pass


@consumer.command()
def ls():
    """Print the consumers configured on the gateway"""
    manager = GatewayManager()
    manager.print_consumers()


@consumer.command()
@click.argument("name")
def add(name):
    """Add a consumer to the gateway"""
    manager = GatewayManager()
    manager.add_consumer(name)


@consumer.command()
@click.argument("name")
def delete(name):
    """Delete a consumer from the gateway"""
    manager = GatewayManager()
    manager.delete_consumer(name)
