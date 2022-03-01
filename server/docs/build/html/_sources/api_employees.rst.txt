Employees API - WORK IN PROGRESS
==================================

This page highlights the different endpoints that are available
to the web interface to interact with employee data and employee hours data.


Usage
~~~~~~

.. http:get:: /api/v1/employees

   An endpoint that retrieves all the employees from the database and formats it into a list.

   **Example request**:

   .. sourcecode:: http

      GET /api/v1/employees HTTP/1.1

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "status": 200,
        "message": "success",
        "data": {
            "employees": [
                {
                    "EmployeeID": "jsmith300",
                    "FirstName": "John",
                    "LastName": "Smith",
                    "PasswordHash": "$2b$12$vS1yUX3qYgrR3PUQhj0/8e55bOiTgU5prMgbaIHxLsD6VkQRtp4kS",
                    "EmployeeEnabled": true,
                    "EntryCreated": "2022-03-01T09:46:58"
                }
            ]
        }
      }


.. http:get:: /api/v1/employees/new

   An endpoint to create a new employee entity and adds it to the employees' table in the database.

   **Example request**:

   .. sourcecode:: http

      GET /api/v1/employees/new HTTP/1.1
      Content-Type: application/json

      {
        "FirstName": "John",
        "LastName": "Smith",
        "RawPassword": "john123"
      }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "status": 201,
        "message": "success",
        "data": {
            "employee": {
                "id": 300,
                "FirstName": "John",
                "PasswordHash": "$2b$12$vS1yUX3qYgrR3PUQhj0/8e55bOiTgU5prMgbaIHxLsD6VkQRtp4kS",
                "EntryCreated": "2022-03-01T09:46:58",
                "EmployeeID": "jsmith300",
                "LastName": "Smith",
                "EmployeeEnabled": true
            }
        }
      }


Implementation Documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: server.web_api.routing.v1.employees.routing
   :members:
   :undoc-members:
   :show-inheritance:
