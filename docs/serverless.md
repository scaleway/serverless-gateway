# Serverless functions

Serverless Functions and Containers can be added to your gateway as a route just like any other URL.

You can try this using the function included at `endpoints/func-example`.

This function uses [Scaleway's Python Serverless API Framework](https://github.com/scaleway/serverless-api-project), which must be installed for the example to work.

Once set up, you can deploy the functions with:

```console
scw-serverless deploy endpoints/func-example/handler.py
```

This will create two URLs, one for the `hello` function and the other one for the `goodbye` function.
