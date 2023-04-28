import click

from cli.gateway import GatewayManager
from cli.model import Route
from cli.infra import InfraManager

LOCAL_FLAG = click.option(
    "-l",
    "--local",
    required=False,
    is_flag=True,
    help="Run against local deployment",
)


def _get_manager(local):
    if local:
        return GatewayManager("http://localhost:8001")
    else:
        click.secho("Not implemented for non-local", fg="red", bold=True)
        raise click.Abort()


@click.group()
def cli():
    pass


@cli.command()
@LOCAL_FLAG
def get_routes(local):
    manager = _get_manager(local)
    routes = manager.get_routes()
    print(routes)


@cli.command()
@click.argument("relative_url")
@click.argument("target")
@LOCAL_FLAG
def add_route(relative_url, target, local):
    manager = _get_manager(local)

    route = Route(relative_url, target)
    manager.add_route(route)


@cli.command()
@click.argument("relative_url")
@click.argument("target")
@LOCAL_FLAG
def delete_route(relative_url, target, local):
    manager = _get_manager(local)

    route = Route(relative_url, target)
    manager.delete_route(route)


@cli.command()
def deploy_containers():
    manager = InfraManager()
    manager.deploy_containers()


@cli.command()
def delete_containers():
    manager = InfraManager()
    manager.delete_containers()


@cli.command()
def get_gateway_host():
    manager = InfraManager()
    manager.get_gateway_host()


@cli.command()
def get_gateway_admin_host():
    manager = InfraManager()
    manager.get_gateway_admin_host()


@cli.command()
def create_db():
    manager = InfraManager()
    manager.create_db()


@cli.command()
def create_namespace():
    manager = InfraManager()
    manager.create_namespace()


@cli.command()
def check_namespace():
    manager = InfraManager()
    manager.check_namespace()


@cli.command()
def delete_namespace():
    manager = InfraManager()
    manager.delete_namespace()


@cli.command()
def create_containers():
    manager = InfraManager()
    manager.create_containers()


@cli.command()
def check_containers():
    manager = InfraManager()
    manager.check_containers()


@cli.command()
def set_custom_domain():
    manager = InfraManager()
    manager.set_custom_domain()


@cli.command()
def update_container():
    manager = InfraManager()
    manager.update_container()


@cli.command()
def update_container_without_deploy():
    manager = InfraManager()
    manager.update_container_without_deploy()
