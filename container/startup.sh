#!/bin/bash

# Start nginx
echo "Starting NGINX"
nginx -g 'daemon off;' &

# Start the Flask server
echo "Starting Flask"
cd /scw-gateway
poetry run flask --app scw_gateway/app.py run &

# Wait for any process to exit
echo "Waiting for exit"
wait -n

# Exit with status of process that exited first
exit $?

