#!/bin/bash

set -em

# Run migrations only from the admin container
if [ ! -z "$IS_ADMIN_CONTAINER" ]; then
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
    
    if [ ! -z "$FORWARD_METRICS" ]; then
        echo "Starting Grafana Agent"
        /scripts/run-grafana-agent.sh
    fi
    
    fg %1
fi

