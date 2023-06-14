# Using Kong directly

The Kong API runs in a private [Scaleway Serverless Container](https://www.scaleway.com/en/serverless-containers/).

Once you have set up your gateway and configured your local config with:

```
scwgw remote-config
```

You can find the URL and token for accessing the admin endpoint in your config file at `~/.config/scw/gateway.yml`:

```
gw_admin_host: <your Kong admin API host>
gw_admin_token: <your admin token>
```

You can then make API requests to your admin endpoint using your admin token as the `X-Auth_Token` header.
