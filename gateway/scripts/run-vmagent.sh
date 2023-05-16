#!/bin/bash

set -e

# Reference: https://docs.victoriametrics.com/Single-server-VictoriaMetrics.html#how-to-send-data-from-graphite-compatible-agents-such-as-statsd
# This will start a statsd server on port 8125 and will send the data to Prometheus
/vmagent          \
    -influxListenAddr=:8125 \
    -remoteWrite.url \
    "https://metrics.cockpit.fr-par.scw.cloud/api/v1/push" \
    -remoteWrite.forcePromProto \
    -remoteWrite.bearerToken \
    "1wSkAPk6qDmtAL1rUJJhwMHhmBp4c0K83qK1UOpOMzz-mS344mXRaCRoPJUUYgbo" \
    -remoteWrite.tmpDataPath \
    "/tmp/vmagent"