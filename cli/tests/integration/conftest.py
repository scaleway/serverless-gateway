import os

import pytest

from tests.integration.environment import IntegrationEnvironment


@pytest.fixture(scope="session")
def integration_env() -> IntegrationEnvironment:
    if os.getenv("DEPLOY_ENV") == "scw":
        return IntegrationEnvironment.get_scw_env()
    return IntegrationEnvironment.get_docker_compose_env()
