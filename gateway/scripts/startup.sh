#!/bin/bash

set -em

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
    # Reference: https://docs.docker.com/config/containers/multi-service_container/
    kong start -v -c /kong-conf/kong.conf &
    
    echo "Starting vm-agent"
    /scripts/run-vmagent.sh
    
    fg %1
fi

