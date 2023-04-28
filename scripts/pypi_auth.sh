#!/bin/bash

set -e

if [ -z $1 ]; then
    echo "Looking up PyPI token from vault"
    PYPI_TOKEN=$(vault kv get -field PYPI_TOKEN fnc_kv/serverless-api-gateway)
else
    echo "Using PyPI token from commandline"
    PYPI_TOKEN=$1
fi

poetry config pypi-token.pypi ${PYPI_TOKEN}
