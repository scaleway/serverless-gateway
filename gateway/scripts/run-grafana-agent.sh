#!/bin/bash

set -e

/bin/grafana-agent                      \
    --config.expand-env                 \
    --config.file=/etc/agent/agent.yaml