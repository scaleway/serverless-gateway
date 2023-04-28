#!/bin/bash

set -e

pushd cli >> /dev/null

poetry build
poetry publish

popd >> /dev/null
