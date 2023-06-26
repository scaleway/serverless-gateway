# Authorization

The Serverless Gateway gives you a standard instance of Kong, which you can configure as you would any other Kong instance (see [kong.md](kong.md)).

A list of Kong authentication plugins can be found in the [Kong Hub](https://docs.konghq.com/hub/?category=authentication). This includes basic auth, JWT, mTLS, and OAuth.

We provide extra CLI support for configuring JWT auth on your routes, as discussed below.

## JWT

### Create a route autorized with JWT

To set up JWT auth on your routes, we use the [Kong JWT plugin](https://docs.konghq.com/hub/kong-inc/jwt/).

First we can create a route with a relative URL `/app` with JWT auth:

```shell
scwgw add-route /app https://www.scaleway.com --jwt
```

Calling it is unauthorized without a token:

```shell
ENDPOINT=https://$(scwgw get-endpoint)
curl ${ENDPOINT}/app

# output
{"message":"Unauthorized"}
```

### Create a consumer with credentials

Access to JWT-protected routes is associated with a [_Consumer_](https://docs.konghq.com/gateway/latest/admin-api/#consumer-object), which represents a user or application. This consumer holds the public and private keys used to generate and sign tokens.

We can add a consumer `my-app` with:

```shell
scwgw add-consumer my-app
```

Then we can generate JWT credentials for this consumer with:

```shell
scwgw add-jwt my-app
```

Which gives an output:

```shell
{
 'algorithm': 'HS256',
 'consumer': {'id': 'd4c0c3ab-ea83-494b-aed2-3717647426c4'},
 'created_at': 1687794681,
 'id': '2573bab2-2d49-4b31-b96a-4c5a8080407e',
 'key': 'YyXIAIlmFf1Fa4sLg2wJGBwH5ESsovBy',
 'rsa_public_key': None,
 'secret': 'o2eQQg2xF5FITEz17VatRlqrZzQMpMZg',
 'tags': None
}
```

You can get all JWT credentials for the consumer with:

```shell
scwgw get-jwts my-app
```

With the secret generated in this request, users can sign requests to access the API.

*NOTE* that the `key` field on this credential is needed for the _issuer_ (`iss`) field in all tokens.

### Signing a request

Signing requests is the responsibility of the client for your API. We can demonstrate an example here using [`PyJWT`](https://github.com/jpadilla/pyjwt).

Taking the secret generated above, we can create an encoded request as follows:

```python
import jwt

SECRET = "o2eQQg2xF5FITEz17VatRlqrZzQMpMZg"

# Note we are using the same algorithm as the credentials
encoded = jwt.encode(
  {
    "some": "payload",
    "iss": "YyXIAIlmFf1Fa4sLg2wJGBwH5ESsovBy"
  },
  SECRET,
  algorithm="HS256"
)

print(encoded)
```

Gives output:

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzb21lIjoicGF5bG9hZCIsImlzcyI6Ill5WElBSWxtRmYxRmE0c0xnMndKR0J3SDVFU3NvdkJ5In0.lkxltveJ2ZQjrdQ7D41UWknNgKCAEfeaqO-8K3z2jHk
```

The resulting encoded token can be passed as a header to our endpoint:

```
curl ${ENDPOINT}/app \
    -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzb21lIjoicGF5bG9hZCIsImlzcyI6Ill5WElBSWxtRmYxRmE0c0xnMndKR0J3SDVFU3NvdkJ5In0.lkxltveJ2ZQjrdQ7D41UWknNgKCAEfeaqO-8K3z2jHk'
```

And we will see our request go through to the upstream.
