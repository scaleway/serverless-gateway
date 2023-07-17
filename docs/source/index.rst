Scaleway Serverless Gateway
===========================

The Scaleway Serverless Gateway is a self-hosted API gateway that runs on `Scaleway Serverless Containers <https://www.scaleway.com/en/serverless-containers/>`_ and `Scaleway Managed Database <https://www.scaleway.com/en/database/>`_.

It lets you manage routing from a single base URL, as well as handle transversal concerns such as CORS and authentication.

It is built on `Kong Gateway <https://konghq.com/>`_, giving you access to the Kong plugin ecosystem to customize your own deployments.

Quickstart
----------

Installation
^^^^^^^^^^^^

.. code-block:: console

    pip install scw-gateway

This will install ``scwgw``, and you can see the list of available commands with:

.. code-block:: console

    scwgw --help

From here you can set up your gateway with:

.. code-block:: console

    scwgw infra deploy

Once the setup process has finished, you can then manage routes as follows:

.. code-block:: bash

    # Check no routes are configured initially
    scwgw route ls

    # Check the response directly from a given URL
    TARGET_URL=http://worldtimeapi.org/api/timezone/Europe/Paris
    curl $TARGET_URL

    # Add a route to this URL in your gateway
    scwgw route add /time $TARGET_URL

    # List routes to see that it's been configured
    scwgw route ls

    # Curl the URL via the gateway
    GATEWAY_ENDPOINT=$(scwgw infra endpoint)
    curl https://${GATEWAY_ENDPOINT}/time

.. Hidden TOC

.. toctree::
   :caption: Contents
   :maxdepth: 2
   :hidden:

   architecture
   auth
   changelog
   cors
   deployment
   development
   domains
   kong
   observability
   serverless

