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
                    "employee_id": "jsmith300",
                    "first_name": "John",
                    "last_name": "Smith",
                    "password_hash": "$2b$12$vS1yUX3qYgrR3PUQhj0/8e55bOiTgU5prMgbaIHxLsD6VkQRtp4kS",
                    "is_enabled": true,
                    "entry_created": "2022-03-01T09:46:58"
                }
            ]
        }
      }


.. http:post:: /api/v1/employees/new

   An endpoint to create a new employee entity and adds it to the employees' table in the database.

   **Example request**:

   .. sourcecode:: http

      POST /api/v1/employees/new HTTP/1.1
      Content-Type: application/json

      {
        "first_name": "John",
        "last_name": "Smith",
        "plain_password": "john123"
      }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 201 OK
      Content-Type: application/json

      {
        "status": 201,
        "message": "success",
        "data": {
            "employee": {
                "id": 300,
                "employee_id": "jsmith300",
                "first_name": "John",
                "last_name": "Smith",
                "password_hash": "$2b$12$vS1yUX3qYgrR3PUQhj0/8e55bOiTgU5prMgbaIHxLsD6VkQRtp4kS",
                "is_enabled": true,
                "entry_created": "2022-03-01T09:46:58"
            }
        }
      }


.. http:post:: /api/v1/employees/verify

   An endpoint to verify the password of an employee with the hashed password stored in the database.

   **Example request**:

   .. sourcecode:: http

      POST /api/v1/employees/verify HTTP/1.1
      Content-Type: application/json

      {
        "employee_id": "jsmith300",
        "password_text": "john123"
      }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "status": 200,
        "message": "success",
        "data": {
            "verified": true
        }
      }


.. http:post:: /api/v1/employees/hours/add

   An endpoint to add work hours to an employee for a given date in YYYY-MM-DD format.

   **Example request**:

   .. sourcecode:: http

      POST /api/v1/employees/hours/add HTTP/1.1
      Content-Type: application/json

      {
        "employee_id": "jsmith300",
        "hours_worked": 8,
        "date_worked": "2022-02-20"
      }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 201 OK
      Content-Type: application/json

      {
        "status": 201,
        "message": "success",
        "data": {
            "employee_hours": {
                "DateWorked": "2022-02-20",
                "HoursWorked": 8,
                "EntryCreated": "2022-03-01T20:22:35",
                "EmployeeID": "jsmith300",
                "id": 50
            }
        }
      }

Implementation Documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: server.web_api.routing.v1.employees.routing
   :members:
   :undoc-members:
   :show-inheritance:
