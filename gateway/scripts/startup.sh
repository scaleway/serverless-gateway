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
    if [ ! -z "$FORWARD_METRICS" ]; then
        echo "Starting Grafana Agent in background"
        /scripts/run-grafana-agent.sh &
    fi

    echo "Starting Kong"

    # Reference: https://docs.docker.com/config/containers/multi-service_container/
    # We need to retry here to give the admin container time to apply database migrations
    for i in 1 2 3 4 5;
    do
        kong start -v -c /kong-conf/kong.conf && break || sleep 30;
    done
fi

