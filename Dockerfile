FROM nginx:1.23.3-alpine

COPY ./generate-nginx-conf.sh /docker-entrypoint.d/10-default-nginx-conf-from-env.sh

# Created here: https://github.com/nginxinc/docker-nginx/blob/5ce65c3efd395ee2d82d32670f233140e92dba99/mainline/alpine-slim/Dockerfile
ARG UID=101

# Implement changes required to run NGINX as an unprivileged user
RUN mkdir -p /etc/nginx/templates/ \
    && chown -R $UID:0 /var/cache/nginx \
    && chmod -R g+w /var/cache/nginx \
    && chown -R $UID:0 /etc/nginx \
    && chmod -R g+w /etc/nginx

COPY templates/ /etc/nginx/templates
COPY helpers/ /etc/nginx/helpers

USER $UID

STOPSIGNAL SIGQUIT
CMD ["nginx", "-g", "daemon off;"]
