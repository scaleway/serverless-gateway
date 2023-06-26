#!/bin/bash

set -e

pushd cli >> /dev/null

cp -n ../README.md .

poetry build
poetry publish

popd >> /dev/null
