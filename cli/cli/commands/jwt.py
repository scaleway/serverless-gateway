import click
from cli.gateway import GatewayManager


@click.group()
def jwt():
    """Manage JWT credentials"""
    pass


@jwt.command()
@click.argument("consumer")
def add(consumer):
    """Adds a JWT credential to a consumer"""
    manager = GatewayManager()
    cred = manager.add_jwt_cred(consumer)
    manager.print_jwt_cred(cred)


@jwt.command()
@click.argument("consumer")
def list(consumer):
    """Lists the JWT credentials for a consumer"""
    manager = GatewayManager()
    manager.print_jwt_creds(consumer)
