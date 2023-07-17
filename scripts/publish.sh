#!/bin/bash

set -e

# Create a dry-run flag to publish to test.pypi.org
DRY_RUN=false
# Parse dry-run from command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo "Unknown argument: $key"
            exit 1
            ;;
    esac
done

pushd cli >> /dev/null

if [ "$DRY_RUN" = true ]; then
    poetry config repositories.testpypi https://test.pypi.org/legacy/
    poetry config pypi-token.testpypi $TEST_PYPI_TOKEN
    echo "Publishing to test.pypi.org"
else 
    echo "Publishing to pypi.org"
fi

# Copy README.md to cli directory
cp -f ../README.md .
# Copy CHANGELOG.md to cli directory
cp -f ../CHANGELOG.md .

# Remove the TOC from the README
# It's delimited by two no toc comments
sed -i '/<!-- no toc -->/,/<!-- no toc -->/d' README.md

poetry build

if [ "$DRY_RUN" = true ]; then
    poetry publish -r testpypi
else
    poetry publish
fi

# Restore the README if git is installed
# This is for convenience when developing
if command -v git &> /dev/null
then
    git checkout -- README.md
fi

popd >> /dev/null
