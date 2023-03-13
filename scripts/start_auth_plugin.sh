#!/bin/bash
set -e

THIS_DIR=$(dirname $(readlink -f $0))
PROJ_ROOT=${THIS_DIR}/..

pushd ${PROJ_ROOT} > /dev/null

python3 -m gateway.plugins.auth --no-lua-style "$@"

popd > /dev/null
