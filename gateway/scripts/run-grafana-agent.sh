#!/bin/bash

set -e

# We sleep here as we need to give the gateway time to start
sleep 20

/bin/grafana-agent                      \
    --config.expand-env                 \
    --config.file=/etc/agent/agent.yaml
