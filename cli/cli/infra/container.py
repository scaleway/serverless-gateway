import scaleway.container.v1beta1 as sdk

from cli.conf import DB_DATABASE_NAME
from cli.infra.image import IMAGE_TAG
from cli.infra.rdb import DB_USERNAME

CONTAINER_NAMESPACE = "scw-sls-gw"

CONTAINER_NAME = "scw-sls-gw"
CONTAINER_MIN_SCALE = 1
CONTAINER_MAX_SCALE = 5
CONTAINER_MEMORY_LIMIT = 1024

CONTAINER_ADMIN_NAME = "scw-sls-gw-admin"
CONTAINER_ADMIN_MIN_SCALE = 1
CONTAINER_ADMIN_MAX_SCALE = 1
CONTAINER_ADMIN_MEMORY_LIMIT = 1024
CONTAINER_ADMIN_PORT = 8001


def create_namespace(api: sdk.ContainerV1Beta1API) -> sdk.Namespace:
    """Create a namespace for the containers."""
    return api.create_namespace(
        name=CONTAINER_NAMESPACE,
    )


def get_namespace_by_name(
    api: sdk.ContainerV1Beta1API, namespace_name: str
) -> sdk.Namespace | None:
    """Get a namespace by its name."""
    namespaces = api.list_namespaces_all(
        name=namespace_name,
    )
    if not namespaces:
        return None

    return namespaces[0]


def get_container_by_name(
    api: sdk.ContainerV1Beta1API, namespace_id: str, container_name: str
) -> sdk.Container | None:
    """Get a container by its name."""
    containers = api.list_containers_all(
        namespace_id=namespace_id,
        name=container_name,
    )
    if not containers:
        return None

    return containers[0]


def get_base_container_env_vars(db_host: str, db_port: int) -> dict[str, str]:
    """Get the base environment variables for the container."""
    return {
        "KONG_PG_HOST": db_host,
        "KONG_PG_PORT": str(db_port),
        "KONG_PG_DATABASE": DB_DATABASE_NAME,
        "KONG_PG_USER": DB_USERNAME,
    }


def get_base_secret_env_vars(db_password: str) -> list[sdk.Secret]:
    """Get the secret environment variables for the container."""
    return [
        sdk.Secret(key="KONG_PG_PASSWORD", value=db_password),
    ]


def create_kong_container(
    api: sdk.ContainerV1Beta1API,
    namespace_id: str,
    db_host: str,
    db_port: int,
    db_password: str,
    metrics_token: str | None,
    metrics_push_url: str | None,
) -> sdk.Container:
    """Create the Kong container."""
    env_vars = get_base_container_env_vars(db_host=db_host, db_port=db_port)
    secret_env_vars = get_base_secret_env_vars(db_password=db_password)

    if metrics_token and metrics_push_url:
        secret_env_vars.append(sdk.Secret("COCKPIT_METRICS_TOKEN", metrics_token))
        env_vars["FORWARD_METRICS"] = "1"
        env_vars["COCKPIT_METRICS_PUSH_URL"] = metrics_push_url

    return api.create_container(
        namespace_id=namespace_id,
        name=CONTAINER_NAME,
        memory_limit=CONTAINER_MEMORY_LIMIT,
        min_scale=CONTAINER_MIN_SCALE,
        max_scale=CONTAINER_MAX_SCALE,
        privacy=sdk.ContainerPrivacy.PUBLIC,
        protocol=sdk.ContainerProtocol.HTTP1,
        http_option=sdk.ContainerHttpOption.REDIRECTED,
        registry_image=IMAGE_TAG,
        environment_variables=env_vars,
        secret_environment_variables=secret_env_vars,
    )


def create_kong_admin_container(
    api: sdk.ContainerV1Beta1API,
    namespace_id: str,
    db_host: str,
    db_port: int,
    db_password: str,
) -> sdk.Container:
    """Create the Kong admin container."""
    env_vars = get_base_container_env_vars(db_host=db_host, db_port=db_port)
    env_vars["IS_ADMIN_CONTAINER"] = "1"

    secret_env_vars = get_base_secret_env_vars(db_password=db_password)

    return api.create_container(
        namespace_id=namespace_id,
        name=CONTAINER_ADMIN_NAME,
        memory_limit=CONTAINER_ADMIN_MEMORY_LIMIT,
        min_scale=CONTAINER_ADMIN_MIN_SCALE,
        max_scale=CONTAINER_ADMIN_MAX_SCALE,
        port=CONTAINER_ADMIN_PORT,
        privacy=sdk.ContainerPrivacy.PRIVATE,
        protocol=sdk.ContainerProtocol.HTTP1,
        http_option=sdk.ContainerHttpOption.REDIRECTED,
        registry_image=IMAGE_TAG,
        environment_variables=env_vars,
        secret_environment_variables=secret_env_vars,
    )


def update_kong_container(
    api: sdk.ContainerV1Beta1API,
    container_id: str,
    db_host: str,
    db_port: int,
    db_password: str,
    metrics_token: str | None,
    metrics_push_url: str | None,
) -> sdk.Container:
    """Create the Kong container."""
    env_vars = get_base_container_env_vars(db_host=db_host, db_port=db_port)
    secret_env_vars = get_base_secret_env_vars(db_password=db_password)

    if metrics_token and metrics_push_url:
        secret_env_vars.append(sdk.Secret("COCKPIT_METRICS_TOKEN", metrics_token))
        env_vars["FORWARD_METRICS"] = "1"
        env_vars["COCKPIT_METRICS_PUSH_URL"] = metrics_push_url

    return api.update_container(
        container_id=container_id,
        memory_limit=CONTAINER_MEMORY_LIMIT,
        min_scale=CONTAINER_MIN_SCALE,
        max_scale=CONTAINER_MAX_SCALE,
        privacy=sdk.ContainerPrivacy.PUBLIC,
        protocol=sdk.ContainerProtocol.HTTP1,
        http_option=sdk.ContainerHttpOption.REDIRECTED,
        registry_image=IMAGE_TAG,
        environment_variables=env_vars,
        secret_environment_variables=secret_env_vars,
    )


def update_kong_admin_container(
    api: sdk.ContainerV1Beta1API,
    container_id: str,
    db_host: str,
    db_port: int,
    db_password: str,
) -> sdk.Container:
    """Create the Kong admin container."""
    env_vars = get_base_container_env_vars(db_host=db_host, db_port=db_port)
    env_vars["IS_ADMIN_CONTAINER"] = "1"

    secret_env_vars = get_base_secret_env_vars(db_password=db_password)

    return api.update_container(
        container_id=container_id,
        memory_limit=CONTAINER_ADMIN_MEMORY_LIMIT,
        min_scale=CONTAINER_ADMIN_MIN_SCALE,
        max_scale=CONTAINER_ADMIN_MAX_SCALE,
        port=CONTAINER_ADMIN_PORT,
        privacy=sdk.ContainerPrivacy.PRIVATE,
        protocol=sdk.ContainerProtocol.HTTP1,
        http_option=sdk.ContainerHttpOption.REDIRECTED,
        registry_image=IMAGE_TAG,
        environment_variables=env_vars,
        secret_environment_variables=secret_env_vars,
    )
