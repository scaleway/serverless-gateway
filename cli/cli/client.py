from scaleway import Client
from scaleway_core.bridge import region

DEFAULT_API_REGION = region.REGION_FR_PAR


def get_scaleway_client() -> Client:
    """Create a Scaleway client."""
    scw_client = Client.from_config_file_and_env()
    if not scw_client.default_region:
        scw_client.default_region = DEFAULT_API_REGION
    return scw_client
