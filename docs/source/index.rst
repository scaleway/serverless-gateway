Serverless Gateway
========================

The Scaleway Serverless Gateway is a self-hosted API gateway that runs on `Scaleway Serverless Containers <https://www.scaleway.com/en/serverless-containers/>`_ and `Scaleway Managed Database <https://www.scaleway.com/en/database/>`_.

It lets you manage routing from a single base URL, as well as handle transversal concerns such as CORS and authentication.

It is built on `Kong Gateway <https://konghq.com/>`_, giving you access to the Kong plugin ecosystem to customize your own deployments.

Quickstart
----------

Installation
^^^^^^^^^^^^

.. code-block:: console

    pip install scw-gateway

This will install ``scwgw``:

.. code-block:: console

    scwgw --help

.. Hidden TOC

.. toctree::
   :caption: Contents
   :maxdepth: 2
   :hidden:

   architecture
   auth
   cors
   custom
   development
   domains
   kong
   observability
   serverless
