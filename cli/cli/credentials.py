import base64
import secrets
import string
import zlib

import click
import scaleway.secret.v1alpha1 as sm
from loguru import logger
from scaleway import Client, ScalewayException

# Name of the secret in Scaleway Secret Manager
PASSWORD_NAME = "scw-gw-database-password"
PASSWORD_LENGTH = 32


def generate_database_password() -> str:
    """Generate a random password for the database.

    Made to be compatible with the requirements of Scaleway Database.
    """
    for _ in range(100):
        password = "".join(
            secrets.choice(string.ascii_letters + string.digits + string.punctuation)
            for _ in range(PASSWORD_LENGTH)
        )
        if (
            any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and any(c.isdigit() for c in password)
            and any(c in string.punctuation for c in password)
        ):
            return password
    raise RuntimeError("Could not generate a password")


def store_db_password_to_scaleway_secret(scw_client: Client, db_password: str):
    """Store the password to Scaleway Secret Manager."""
    api = sm.SecretV1Alpha1API(scw_client)
    try:
        secret = api.get_secret_by_name(secret_name=PASSWORD_NAME)
        raise RuntimeError(f"Secret {PASSWORD_NAME} already exists with id {secret.id}")
    except ScalewayException as exception:
        if exception.status_code != 404:
            raise exception

    logger.info("Creating secret for database password")
    secret = api.create_secret(
        name=PASSWORD_NAME,
        tags=["scw-gw"],
        description="Password for the database for scw-gw",
    )

    data = db_password.encode("utf-8")
    api.create_secret_version(
        secret_id=secret.id,
        data=base64.b64encode(data).decode("utf-8"),
        data_crc32=zlib.crc32(data) & 0xFFFFFFFF,
    )


def get_db_password_from_scaleway_secret(scw_client: Client) -> str:
    """Get the password from Scaleway Secret Manager."""
    api = sm.SecretV1Alpha1API(scw_client)
    version = api.access_secret_version_by_name(
        secret_name=PASSWORD_NAME, revision="latest"
    )
    password = base64.b64decode(version.data)
    data_crc32 = zlib.crc32(password) & 0xFFFFFFFF
    if version.data_crc32 and not secrets.compare_digest(
        str(data_crc32), str(version.data_crc32)
    ):
        raise ValueError("CRC32 of data does not match")
    return password.decode("utf-8")


def load_db_password_or_abort(scw_client: Client) -> str:
    """Load the password from Scaleway Secret Manager or abort."""
    logger.debug("Looking for database password in Scaleway Secret Manager")
    try:
        password = get_db_password_from_scaleway_secret(scw_client)
        return password
    except ScalewayException as exception:
        if exception.status_code == 404:
            click.secho(
                "Database password not found in Scaleway Secret Manager", fg="red"
            )
        raise exception
