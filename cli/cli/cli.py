import click

from cli.gateway import GatewayManager
from cli.model import Route
from cli.infra import InfraManager


@click.group()
def cli():
    pass


@cli.command()
def local_config():
    """Sets up config for local deployment"""
    manager = InfraManager()
    manager.set_up_config(True)


@cli.command()
def remote_config():
    """Sets up config for remote deployment"""
    manager = InfraManager()
    manager.set_up_config(False)


@cli.command()
def get_routes():
    """Returns the routes configured on the gateway"""
    manager = GatewayManager()
    routes = manager.get_routes()
    print(routes)


@cli.command()
@click.argument("relative_url")
@click.argument("target")
def add_route(relative_url, target):
    """Adds a route to the gateway"""
    manager = GatewayManager()

    route = Route(relative_url, target)
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
def create_admin_token():
    """Creates a token for the admin container"""
    manager = InfraManager()
    token = manager.create_admin_container_token()
    click.secho(token)


@cli.command()
def delete_containers():
    """Deletes the containers used for the gateway"""
    manager = InfraManager()
    manager.delete_containers()


@cli.command()
def get_gateway_endpoint():
    """Returns the endpoint for the gateway"""
    manager = InfraManager()
    endpoint = manager.get_gateway_endpoint()
    click.secho(endpoint)


@cli.command()
def get_gateway_admin_endpoint():
    """Returns the endpoint for the gateway admin"""
    manager = InfraManager()
    endpoint = manager.get_gateway_admin_endpoint()
    click.secho(endpoint)


@cli.command()
def create_db():
    """Creates the database for the gateway"""
    manager = InfraManager()
    manager.create_db()


@cli.command()
def check_db():
    """Checks the status of the database"""
    manager = InfraManager()
    manager.check_db()


@cli.command()
def await_db():
    """Waits for the database to be ready"""
    manager = InfraManager()
    manager.await_db()


@cli.command()
def create_namespace():
    """Creates the container container namespace"""
    manager = InfraManager()
    manager.create_namespace()


@cli.command()
def check_namespace():
    """Checks the status of the container namespace"""
    manager = InfraManager()
    manager.check_namespace()


@cli.command()
def await_namespace():
    """Waits for the namespace to be ready"""
    manager = InfraManager()
    manager.await_namespace()


@cli.command()
def delete_namespace():
    """Deletes the container namespace"""
    manager = InfraManager()
    manager.delete_namespace()


@cli.command()
def create_containers():
    """Creates the containers"""
    manager = InfraManager()
    manager.create_containers()


@cli.command()
def check_containers():
    """Checks the status of the containers"""
    manager = InfraManager()
    manager.check_containers()


@cli.command()
def await_containers():
    """Waits for the containers to be ready"""
    manager = InfraManager()
    manager.await_containers()


@cli.command()
def set_custom_domain():
    """Sets the custom domain for the gateway container"""
    manager = InfraManager()
    manager.set_custom_domain()


@cli.command()
def update_containers():
    """Updates the containers"""
    manager = InfraManager()
    manager.update_container()


@cli.command()
def update_container_no_deploy():
    """Updates the containers without redeploying"""
    manager = InfraManager()
    manager.update_container_without_deploy()
