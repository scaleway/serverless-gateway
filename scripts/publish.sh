#!/bin/bash

set -e

pushd cli >> /dev/null

cp -f ../README.md .

poetry build
poetry publish

popd >> /dev/null
