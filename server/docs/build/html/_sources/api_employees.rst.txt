Employees API
===============

This page highlights the different endpoints that are available
to the web interface to interact with employee data.


Usage
~~~~~~

..  http:get:: /api/v1/employees/count

    An endpoint that counts the number of employees registered in the database and returns it in the response.

    :status 200: When the total number of employees is successfully retrieved from the database.

    **Example request**:

    .. sourcecode:: http

        GET /api/v1/employees/count HTTP/1.1

        Headers:
        {
            "Authorization": "Bearer <access_token>"
        }

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

..  http:get:: /api/v1/employees/all

    An endpoint that retrieves all the employees from the database and formats it into a list.

    :status 200: When the list of employees is successfully retrieved from the database.

    **Example request**:

    .. sourcecode:: http

        GET /api/v1/employees/all HTTP/1.1

        Headers:
        {
            "Authorization": "Bearer <access_token>"
        }

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
                        "is_enabled": true
                    },
                    {
                        "employee_id": jsmith301",
                        "first_name": "Johnny",
                        "last_name": "Smith",
                        "is_enabled": false
                    }
                ]
            }
        }

..  http:get:: /api/v1/employees

    An endpoint that retrieves multiple specific employees from the database and formats it into a list.

    :param employee_ids: A list of employee IDs to retrieve employees from the database.
    :status 200: When the list of employees is successfully retrieved from the database.

    **Example request**:

    .. sourcecode:: http

        GET /api/v1/employees HTTP/1.1

        Headers:
        {
            "Authorization": "Bearer <access_token>"
        }
        Body:
        {
            "employee_ids": ["jsmith300", "jsmith301"]
        }

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
                        "is_enabled": true
                    },
                    {
                        "employee_id": jsmith301",
                        "first_name": "Johnny",
                        "last_name": "Smith",
                        "is_enabled": false
                    }
                    ......
                ]
            }
        }


..  http:get:: /api/v1/employees/:{employee_id}:

    An endpoint that retrieves detailed employee information from the database by providing the ID in the URL.

    :status 200: When the detailed employee information is successfully retrieved from the database.

    **Example request**:

    .. sourcecode:: http

        GET /api/v1/employees/:{employee_id}: HTTP/1.1

        URL: <server_url>/api/v1/employees/jsmith317
        Headers:
        {
            "Authorization": "Bearer <access_token>"
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
                    "employee_id": "jsmith317",
                    "first_name": "john",
                    "last_name": "smith",
                    "role": "employee",
                    "full_name_of_contact": "john smith",
                    "primary_email": "johnsmith123@email.com",
                    "secondary_email": null,
                    "enable_notifications": true,
                    "is_enabled": true
                }
            }
        }


..  http:get:: /api/v1/employees/token

    An endpoint that retrieves basic employee information such as the employee ID, first name, last name, and status from the access token.

    :status 200: When the employee is successfully retrieved from the database.

    **Example request**:

    .. sourcecode:: http

        GET /api/v1/employees/token HTTP/1.1

        Headers:
        {
            "Authorization": "Bearer <access_token>"
        }

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "status": 200,
            "message": "success",
            "data": {
                "employees": {
                    "employee_id": "jsmith317",
                    "first_name": "john",
                    "last_name": "smith",
                    "role": "employee",
                    "full_name_of_contact": "john smith",
                    "primary_email": "johnsmith123@email.com",
                    "secondary_email": null,
                    "enable_notifications": true,
                    "is_enabled": true
                }
            }
        }


..  http:post:: /api/v1/employees

    An endpoint to create a new employee entity and adds it to the employees' table in the database.

    :param first_name: The first name of the new employee.
    :param last_name: The last name of the new employee.
    :param plain_password: The plain-text password for the next employee account.
    :param primary_email: The primary email contact for the employee.
    :param secondary_email [Optional]: The secondary email contact for the employee.
    :param enable_notifications [Optional]: Enable or disable email notifications, enabled by default.
    :param is_enabled [Optional]: Enable or disable the new account, enabled by default.
    :status 201: When the employee is successfully created and registered in the database.
    :status 400: When the request body contains invalid parameters, or the employee already exists in the database.

    **Example request**:

    .. sourcecode:: http

        POST /api/v1/employees/new HTTP/1.1
        Headers:
        {
            "Authorization": "Bearer <access_token>"
        }
        Body:
        {
            "first_name": "John",
            "last_name": "Smith",
            "plain_password": "john123",
            "role": "employee"
            "primary_email": "johnsmith123@email.com",
            [OPTIONAL] "secondary_email": null,
            [OPTIONAL] "enable_notifications": true,
            [OPTIONAL] "is_enabled": true
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
                    "employee_id": "jsmith318",
                    "first_name": "john",
                    "last_name": "smith",
                    "role_name": "employee",
                    "primary_email": "johnsmith123@email.com",
                    "secondary_email": null,
                    "email_notifications_enabled": true,
                    "is_enabled": true
                }
            }
        }


..  http:delete:: /api/v1/employees

    An endpoint to delete an existing employee record from the database.

    :param employee_ids: The employee IDs of the employees to be removed provided as a list. If only one employee needs to be deleted, it can be provided as a string.
    :status 201: When the employee is successfully deleted from the database.
    :status 400: When the request body contains invalid parameters, or the employee does not exist in the database.

    **Example request**:

    .. sourcecode:: http

        DELETE /api/v1/employees HTTP/1.1
        Headers:
        {
            "Authorization": "Bearer <access_token>"
        }
        Body:
        {
            "employee_ids": "jsmith300"
            [OR]
            "employee_ids": ["jsmith300", "jsmith301", "jsmith302"]
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
                    "employee_id": "jsmith300",
                    "first_name": "John",
                    "last_name": "Smith",
                    "is_enabled": true,
                    "entry_created": "2022-03-01T09:46:58"
                }
            }
        }


Implementation Documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: server.web_api.routing.v1.employee_routing
   :members:
   :undoc-members:
   :show-inheritance:
