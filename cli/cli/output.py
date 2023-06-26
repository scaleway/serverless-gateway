import click
import json


def pretty_print_dict(d: dict):
    d_str = json.dumps(d, indent=4)
    click.secho(d_str)
