#!/bin/sh

echo -n $NGINX_CONF_B64 | base64 -d > /etc/nginx/nginx.conf
cat /etc/nginx/nginx.conf

