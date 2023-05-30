# Serverless functions

Serverless Functions and Containers can be added to your gateway as a route just like any other URL.

If you are building a Python serverless app, you can also manage and transparently integrate with your gateway using the [Scaleway Python API framework](https://github.com/scaleway/serverless-api-project), which makes building and managing complex serverless APIs easy.

You can try this using the function included at `endpoints/func-example`.

Once set up, you can deploy the functions with:

```console
scw-serverless deploy endpoints/func-example/handler.py
```

This will create two URLs, one for the `hello` function and the other one for the `goodbye` function.
