API Status
============

This page highlights the different endpoints that are available
to the web interface to interact with the status of the web API.

Usage
~~~~~~

.. http:get:: /api/v1

   An endpoint that checks the status of the v1 segment of the API service.

   :status 200: When the status of API v1 is verified to be enabled.

   **Example request**:

   .. sourcecode:: http

      GET /api/v1 HTTP/1.1

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "status": 200,
        "message": "success",
        "data": {}
      }


.. http:get:: /api/v1/status

   An endpoint that checks the status of the database connection in the server.

   :status 200: When the status of the database connection is retrieved.

   **Example request**:

   .. sourcecode:: http

      GET /api/v1/status HTTP/1.1

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "status": 200,
        "message": "success",
        "data": {
            "status": "online"
        }
      }


Implementation Documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: server.web_api.routing.v1.core_routing
   :members:
   :undoc-members:
   :show-inheritance:
