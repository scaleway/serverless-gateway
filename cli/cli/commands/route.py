import click

from cli.gateway import GatewayManager
from cli.model import Route


@click.group()
def route():
    """Manage gateway routes"""
    pass


@route.command()
def ls():
    """Print the routes configured on the gateway"""
    manager = GatewayManager()
    manager.print_routes()


@route.command()
@click.argument("relative_url")
@click.argument("target")
@click.option(
    "--cors", is_flag=True, default=False, help="Add permissive cors to the route."
)
@click.option("--jwt", is_flag=True, default=False, help="Add JWT auth to the route.")
@click.option(
    "--http-methods",
    "-m",
    help="HTTP methods that the route should accept. Defaults to all if not specified.",
    multiple=True,
)
def add(relative_url: str, target: str, cors: bool, jwt: bool, http_methods: list[str]):
    """Add a route to the gateway"""
    manager = GatewayManager()

    route = Route(
        relative_url=relative_url,
        target=target,
        cors=cors,
        jwt=jwt,
        http_methods=http_methods,
    )
    manager.add_route(route)


@route.command()
@click.argument("relative_url")
@click.argument("target")
def delete(relative_url, target):
    """Delete a route from the gateway"""
    manager = GatewayManager()

    route = Route(relative_url, target)
    manager.delete_route(route)
