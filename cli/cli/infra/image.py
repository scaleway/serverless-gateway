from importlib.metadata import version

IMAGE_REGISTRY = "docker.io"
IMAGE_ORG = "scaleway"
IMAGE_NAME = "serverless-gateway"

# Single source of truth for the image version is the version of the package
IMAGE_VERSION = version("scw-gateway")

IMAGE_TAG = f"{IMAGE_REGISTRY}/{IMAGE_ORG}/{IMAGE_NAME}:{IMAGE_VERSION}"
