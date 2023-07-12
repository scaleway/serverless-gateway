import click
from scaleway_core.profile.env import ENV_KEY_SCW_PROFILE

profile_option = click.option(
    "--profile",
    "-p",
    help=f"""The Scaleway profile to use for this command.
Can also be set with the {ENV_KEY_SCW_PROFILE} environment variable.""",
    required=False,
)

not_interactive_option = click.option(
    "--yes", "-y", is_flag=True, default=False, help="Skip interactive confirmation"
)
