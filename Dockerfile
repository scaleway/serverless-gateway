FROM kong:3.0.2-alpine
USER root

RUN apk update
RUN apk add curl
RUN apk add python3 \
      py3-pip \
      python3-dev

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

WORKDIR /app
COPY . . 

STOPSIGNAL SIGQUIT
ENV KONG_NGINX_DAEMON=off

USER kong
CMD ["kong", "start", "-v", "-c", "/app/container/kong.conf"]

