# Grafana Agent does not use versioned tags for their images, 
# so we use the main branch
FROM grafana/agent:main as agent

FROM kong:3.2.2-alpine

USER root

RUN apk update --no-cache && \
    apk add --no-cache \
    curl \
    # Add libc6-compat to use agent binary in alpine
    libc6-compat \
    && rm -rf /var/cache/apk/*

STOPSIGNAL SIGQUIT

ENV KONG_NGINX_DAEMON=off

ADD scripts /scripts
ADD config/ /kong-conf

RUN mkdir /var/run/kong
RUN chown -R kong:kong /var/run/kong

# Copy the grafana-agent binary from the agent image
COPY --from=agent /bin/grafana-agent /bin/grafana-agent
COPY observability/agent.yaml /etc/agent/agent.yaml
RUN mkdir /tmp/wal && \
    chown -R kong:kong /tmp/wal

USER kong

CMD ["/scripts/startup.sh"]
