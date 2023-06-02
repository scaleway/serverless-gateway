import scaleway.rdb.v1 as sdk

DB_INSTANCE_NAME = "scw-sls-gw"
DB_ENGINE = "PostgreSQL-14"
DB_USERNAME = "kong"
DB_VOLUME_TYPE = "lssd"
DB_NODE_TYPE = "DB-DEV-S"
DB_VOLUME_SIZE = 5000000000  # Expressed in bytes


def create_database_instance(api: sdk.RdbV1API, password: str) -> sdk.Instance:
    """Create a managed database instance."""

    return api.create_instance(
        name=DB_INSTANCE_NAME,
        engine=DB_ENGINE,
        user_name=DB_USERNAME,
        password=password,
        is_ha_cluster=False,
        disable_backup=True,
        backup_same_region=True,
        node_type=DB_NODE_TYPE,
        volume_type=sdk.VolumeType(DB_VOLUME_TYPE),
        volume_size=DB_VOLUME_SIZE,
    )


def get_database_instance_by_name(
    api: sdk.RdbV1API, instance_name: str
) -> sdk.Instance | None:
    """Get a database instance by its name."""

    instances = api.list_instances_all(
        name=instance_name,
    )
    if not instances:
        return None

    return instances[0]
