FROM victoriametrics/vmagent:v1.90.0 as vmagent

FROM kong:3.2.2-alpine

USER root

RUN apk update
RUN apk add curl

STOPSIGNAL SIGQUIT

ENV KONG_NGINX_DAEMON=off

ADD scripts /scripts
ADD config/ /kong-conf

RUN mkdir /var/run/kong
RUN chown -R kong:kong /var/run/kong

# Copy the vmagent binary from the vmagent container
COPY --from=vmagent /vmagent-prod /vmagent
RUN mkdir /tmp/vmagent && \
    chown -R kong:kong /tmp/vmagent

USER kong
CMD ["/scripts/startup.sh"]

