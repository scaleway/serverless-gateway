#!/bin/bash

set -e

pushd cli >> /dev/null

VERSION=$(poetry version -s)
git tag -f v${VERSION}
git push -f --tags

popd >> /dev/null
