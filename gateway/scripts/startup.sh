#!/bin/bash

set -e

# Run migrations only from the admin container
if [ "$IS_ADMIN_CONTAINER" == "1" ]; then
    echo "Running Kong migrations"

    kong migrations bootstrap
    kong migrations up
    kong migrations finish

    echo "Starting Kong admin"
    kong start -v -c /kong-conf/kong-admin.conf
else
    echo "Starting Kong"
    kong start -v -c /kong-conf/kong.conf
fi

