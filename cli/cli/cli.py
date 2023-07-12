import sys

import click
from loguru import logger

from cli.commands.consumer import consumer as consumer_commands
from cli.commands.dev import dev as dev_commands
from cli.commands.domain import domain as domain_commands
from cli.commands.human.errors import display_exception
from cli.commands.infra import infra as infra_commands
from cli.commands.jwt import jwt as jwt_commands
from cli.commands.route import route as route_commands


@click.group()
@click.option(
    "--debug",
    "-d",
    is_flag=True,
    help="Enables debug mode.",
    default=False,
    envvar="DEBUG",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="INFO",
    show_default=True,
    help="Set the log level.",
    envvar="LOG_LEVEL",
)
def cli(debug: bool, log_level: str) -> None:
    """CLI for managing the Scaleway Gateway.
    Documentation is available at:
    https://serverless-gateway.readthedocs.io/en/latest/

    Commands are grouped into subgroups. Run

      scwgw <group> --help

    to see the available commands, and

      scwgw <group> <command>

    to run a specific command.
    """
    # Set log level
    logger.remove()
    logger.add(sys.stderr, level=log_level, backtrace=False)
    if debug:
        logger.add(sys.stderr, level="DEBUG", backtrace=True, diagnose=True)


cli.add_command(consumer_commands)
cli.add_command(dev_commands)
cli.add_command(domain_commands)
cli.add_command(infra_commands)
cli.add_command(jwt_commands)
cli.add_command(route_commands)


def main():
    """Entrypoint for the CLI."""
    try:
        cli()  # pylint: disable=no-value-for-parameter
    except Exception as err:  # pylint: disable=broad-except
        # Print the exception in the console
        logger.opt(exception=err).debug("An error occurred")
        display_exception(err)


if __name__ == "__main__":
    main()
