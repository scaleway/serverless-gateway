import sys

import click
from loguru import logger

from cli.commands.consumer import consumer as consumer_commands
from cli.commands.dev import dev as dev_commands
from cli.commands.domain import domain as domain_commands
from cli.commands.infra import infra as infra_commands
from cli.commands.jwt import jwt as jwt_commands
from cli.commands.route import route as route_commands


@click.group()
def cli():
    """CLI for managing the Scaleway gateway.

    Commands are grouped into subgroups. Run

      scwgw <group> --help

    to see the available commands, and

      scwgw <group> <command>

    to run a specific command.
    """
    # Set log level
    logger.remove()
    logger.add(sys.stderr, level="INFO")


cli.add_command(consumer_commands)
cli.add_command(dev_commands)
cli.add_command(domain_commands)
cli.add_command(infra_commands)
cli.add_command(jwt_commands)
cli.add_command(route_commands)
