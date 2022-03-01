Students API - WORK IN PROGRESS
==================================

This page highlights the different endpoints that are available
to the web interface to interact with student data and before-care/after-care services data.

Usage
~~~~~~

.. http:get:: /api/v1/students

   An endpoint that retrieves all the students from the database and formats it into a list.

   **Example request**:

   .. sourcecode:: http

      GET /api/v1/students HTTP/1.1

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "status": 200,
        "message": "success",
        "data": {
            "students": [
                {
                    "student_id": "jjerome4",
                    "first_name": "Jason",
                    "last_name": "Jerome",
                    "is_enabled": true,
                    "entry_created": "2022-03-01T20:40:03"
                }
            ]
        }
      }


.. http:post:: /api/v1/students/new

   An endpoint that creates a new student in the database given a valid first and last name.

   **Example request**:

   .. sourcecode:: http

      POST /api/v1/students HTTP/1.1
      Content-Type: application/json

      {
        "first_name": "Jason",
        "last_name": "Jerome"
      }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 201 OK
      Content-Type: application/json

      {
        "status": 201,
        "message": "success",
        "data": {
            "student": {
                "student_id": "jjerome5",
                "first_name": "Jason",
                "last_name": "Jerome",
                "is_enabled": true,
                "entry_created": "2022-03-01T20:46:14"
            }
        }
      }


Implementation Documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: server.web_api.routing.v1.students.routing
   :members:
   :undoc-members:
   :show-inheritance:
