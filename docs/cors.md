# CORS

When creating routes with the CLI, you can add the `--cors` flag to add permissive CORS.

Under the hood, this uses the Kong [`cors` plugin](https://docs.konghq.com/hub/kong-inc/cors/) to add permissive CORS rules to the underlying `service`.

## Usage

To create a dummy route, we can run:

```
# Make options request to target URL, see no CORS headers
TARGET_URL=http://worldtimeapi.org/api/timezone/Europe/Paris
curl -X OPTIONS -I $TARGET_URL

# Add routes with and without cors
scwgw route add /cors $TARGET_URL --cors
scwgw route add /no-cors $TARGET_URL

# List routes to see that it's been configured
scwgw route list

# Curl the routes with and without CORS to see the difference in headers
GATEWAY_ENDPOINT=$(scwgw infra endpoint)
curl -X OPTIONS -I https://${GATEWAY_ENDPOINT}/cors
curl -X OPTIONS -I https://${GATEWAY_ENDPOINT}/no-cors
```
