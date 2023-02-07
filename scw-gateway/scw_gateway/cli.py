import sys

import click
from loguru import logger

from .container.build import build, push


@click.group()
@click.option(
    "-d",
    "--debug",
    required=False,
    is_flag=True,
    default=False,
    help="Turn debug logging on",
)
def cli(debug):
    logger.remove()
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time}</green> <level>{message}</level>",
        level="DEBUG" if debug else "INFO",
    )


@cli.command()
def container():
    """Builds and pushes the gateway container"""
    build()
    push()
