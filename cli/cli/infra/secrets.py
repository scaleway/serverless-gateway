import base64
import secrets
import string
import zlib

import scaleway.secret.v1alpha1 as sdk
from loguru import logger
from scaleway import ScalewayException

# Name of the secret in Secret Manager
PASSWORD_NAME = "scw-gw-database-password"
PASSWORD_LENGTH = 32


def generate_database_password() -> str:
    """Generate a random password for the database.

    Made to be compatible with the requirements of Managed Database validation.
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


def create_db_password_secret(api: sdk.SecretV1Alpha1API, db_password: str):
    """Store the password to Secret Manager."""

    delete_db_password_secret(api)

    logger.debug("Creating secret for database password")
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


def delete_db_password_secret(api: sdk.SecretV1Alpha1API):
    """Delete the password from Secret Manager."""
    try:
        # Delete password if already exists
        secret = api.get_secret_by_name(secret_name=PASSWORD_NAME)
        logger.debug(f"Deleting {PASSWORD_NAME} secret")
        api.delete_secret(secret_id=secret.id)

    except ScalewayException as exception:
        if exception.status_code != 404:
            raise exception


def get_db_password(api: sdk.SecretV1Alpha1API) -> str:
    """Get the password from Secret Manager."""
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
