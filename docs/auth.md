# Authentication

The Serverless Gateway gives you a standard instance of Kong, so you can configure this as you would any other Kong instance (see [kong.md](kong.md)).

However, we also provide some convenience utils for configuring JWT auth on your routes, as discussed below.

## JWT

To set up JWT auth on your routes, we can use the [Kong JWT plugin](https://docs.konghq.com/hub/kong-inc/jwt/).


