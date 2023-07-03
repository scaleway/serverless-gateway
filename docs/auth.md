# Authentication and authorization

The Serverless Gateway is built on Kong, which you can configure as you would any other Kong instance (see [kong.md](kong.md)).

A list of Kong authentication plugins can be found in the [Kong Hub](https://docs.konghq.com/hub/?category=authentication), and includes basic auth, JWT, mTLS, and OAuth.

We provide extra CLI support for configuring JWT authorization on your routes, as discussed below.

## JWT

### Create a route

To set up JWT on your routes, we use the [Kong JWT plugin](https://docs.konghq.com/hub/kong-inc/jwt/). We can use the CLI to create a route with JWT and a relative URL `/app`:

```shell
scwgw route add /app https://www.scaleway.com --jwt
```

Calling it is unauthorized without a token:

```shell
ENDPOINT=https://$(scwgw infra endpoint)
curl ${ENDPOINT}/app
```

gives output:

```
{"message":"Unauthorized"}
```

### Create a consumer with credentials

Access to JWT-protected routes is associated to a [_Consumer_](https://docs.konghq.com/gateway/latest/admin-api/#consumer-object), which represents a user or application. This consumer holds the public and private keys used to generate and sign tokens.

We can add a consumer called `my-app` with:

```shell
scwgw consumer add my-app
```

Then we can generate JWT credentials for this consumer with:

```shell
scwgw jwt add my-app
```

Which gives an output like:

```shell
ALGORITHM     SECRET                                 ISS
HS256         o2eQQg2xF5FITEz17VatRlqrZzQMpMZg       YyXIAIlmFf1Fa4sLg2wJGBwH5ESsovBy
```

With the secret generated in this request, users can sign requests to access the API.

*NOTE* that you must provide the ISS value in an `iss` field in all encoded tokens.

You can get all JWT credentials for a given consumer with:

```shell
scwgw jwt ls my-app
```

### Signing a request

Using credentials to sign requests is the responsibility of the client making the request. However, we can demonstrate an example here using [`PyJWT`](https://github.com/jpadilla/pyjwt).

Taking the secret generated above, we can create an encoded request as follows:

```python
import jwt

# "Secret" value for the credentials
SECRET = "o2eQQg2xF5FITEz17VatRlqrZzQMpMZg"

encoded = jwt.encode(
  {
    "some": "payload",
    "iss": "YyXIAIlmFf1Fa4sLg2wJGBwH5ESsovBy" # ISS value for the credentials
  },
  SECRET,
  algorithm="HS256"
)

print(encoded)
```

This prints an encoded JWT, which looks something like:

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzb21lIjoicGF5bG9hZCIsImlzcyI6Ill5WElBSWxtRmYxRmE0c0xnMndKR0J3SDVFU3NvdkJ5In0.lkxltveJ2ZQjrdQ7D41UWknNgKCAEfeaqO-8K3z2jHk
```

This can then be passed as a header to our endpoint:

```
curl ${ENDPOINT}/app \
    -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzb21lIjoicGF5bG9hZCIsImlzcyI6Ill5WElBSWxtRmYxRmE0c0xnMndKR0J3SDVFU3NvdkJ5In0.lkxltveJ2ZQjrdQ7D41UWknNgKCAEfeaqO-8K3z2jHk'
```

and we see that our request goes through to the upstream.
