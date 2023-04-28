FROM kong:3.0.2-alpine

USER root

RUN apk update
RUN apk add curl

STOPSIGNAL SIGQUIT

ENV KONG_NGINX_DAEMON=off

COPY scripts/startup.sh /startup.sh
ADD config/ /kong-conf

RUN mkdir /var/run/kong
RUN chown -R kong:kong /var/run/kong

USER kong
CMD ["/startup.sh"]

