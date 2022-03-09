Employees API - WORK IN PROGRESS
==================================

This page highlights the different endpoints that are available
to the web interface to interact with employee data and employee hours data.


Usage
~~~~~~

.. http:get:: /api/v1/employees

   An endpoint that retrieves all the employees from the database and formats it into a list.

   :status 200: When the list of employees is successfully retrieved from the database.

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


.. http:get:: /api/v1/employees/count

   An endpoint that counts the number of employees registered in the database and returns it in the response.

   :status 200: When the total number of employees is successfully retrieved from the database.

   **Example request**:

   .. sourcecode:: http

      GET /api/v1/employees/count HTTP/1.1

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "status": 200,
        "message": "success",
        "data": {
            "count": 1
        }
      }


.. http:post:: /api/v1/employees/new

   An endpoint to create a new employee entity and adds it to the employees' table in the database.

   :param first_name: The first name of the new employee.
   :param last_name: The last name of the new employee.
   :status 201: When the employee is successfully created and registered in the database.
   :status 400: When the request body contains invalid parameters, or the employee already exists in the database.

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


.. http:post:: /api/v1/employees/remove

   An endpoint to delete an existing employee entity from the database.

   :param employee_id: The employee ID of the employee to be removed.
   :status 201: When the employee is successfully deleted from the database.
   :status 400: When the request body contains invalid parameters, or the employee does not exist in the database.

   **Example request**:

   .. sourcecode:: http

      POST /api/v1/employees/new HTTP/1.1
      Content-Type: application/json

      {
        "employee_id": "jsmith300"
      }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "status": 200,
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

   :param employee_id: The employee ID of the employee.
   :param password_text: The plain-text password of the employee attempting to verify their credentials.
   :status 200: When the verification process is successfully completed.
   :status 400: When the employee ID or the provided password is invalid.

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


.. http:get:: /api/v1/employees/hours

   An endpoint that retrieves the total employee work hours from the given date range.

   :param employee_id: The employee ID of the employee.
   :param date_start: The start date of the work hours to query in YYYY-MM-DD format.
   :param date_end: The end date of the work hours to query in YYYY-MM-DD format.
   :status 200: When the total employee work hours are successfully retrieved and calculated.
   :status 400: When the employee ID, start date, or end date is invalid.

   **Example request**:

   .. sourcecode:: http

      GET /api/v1/employees/hours?employee_id=jsmith300&date_start=2022-02-01&date_end=2022-02-22 HTTP/1.1


   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "status": 200,
        "message": "success",
        "data": {
            "hours": 8
        }
      }

.. http:post:: /api/v1/employees/hours/add

   An endpoint to add work hours to an employee for a given date in YYYY-MM-DD format.

   :param employee_id: The employee ID of the employee.
   :param hours_worked: The hours worked by the employee on the provided date.
   :param date_worked: The date the employee worked for the provided hours.
   :status 201: When the employee work hours are successfully added to the database.
   :status 400: When the request body contains invalid parameters.

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

.. automodule:: server.web_api.routing.v1.employee_routing
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: server.web_api.routing.v1.employee_hours_routing
   :members:
   :undoc-members:
   :show-inheritance: