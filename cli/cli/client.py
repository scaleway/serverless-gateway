import os
import typing as t

from loguru import logger
from scaleway import Client
from scaleway_core.bridge import region
from scaleway_core.profile.env import ENV_KEY_SCW_PROFILE

DEFAULT_API_REGION = region.REGION_FR_PAR
DEFAULT_PROFILE_NAME = "default"


def get_scaleway_client(profile_name: t.Optional[str] = None) -> Client:
    """Create a Scaleway client."""
    if not profile_name:
        profile_name = os.getenv(ENV_KEY_SCW_PROFILE, DEFAULT_PROFILE_NAME)
    if profile_name != DEFAULT_PROFILE_NAME:
        logger.debug(f"Using Scaleway profile: {profile_name}")
    scw_client = Client.from_config_file_and_env(profile_name=profile_name)
    if not scw_client.default_region:
        scw_client.default_region = DEFAULT_API_REGION

    # Validate the client
    scw_client.validate()

    return scw_client
