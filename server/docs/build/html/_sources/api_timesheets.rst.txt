Time Sheets API
==================

This page highlights the different endpoints that are available
to the web interface to interact with employee timesheet data.


Usage
~~~~~~

..  http:get:: /api/v1/timesheet/:{employee_id}:

    An endpoint that retrieves the total employee hours and individual time sheets from the given date range.

    :param date_start: The start date of the time sheets to query in YYYY-MM-DD format.
    :param date_end: The end date of the time sheets to query in YYYY-MM-DD format.
    :status 200: When the total employee work hours are successfully retrieved and calculated.
    :status 400: When the employee ID, start date, or end date is invalid.

    **Example request**:

    .. sourcecode:: http

        GET /api/v1/timesheet/:{employee_id}:

        URL: /api/v1/timesheet/jsmith317
        Headers:
        {
            "Authorization": "Bearer <access_token>"
        }
        Body:
        {
            "date_start": "2022-03-01",
            "date_end": "2022-03-30"
        }


   **Example response**:

   .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "status": 200,
            "message": "success",
            "data": {
                "total_hours": {
                    "work_hours": 14,
                    "pto_hours": 6,
                    "extra_hours": 0
                },
                "time_sheets": {
                    "2022-03-01": {
                        "work_hours": 8,
                        "pto_hours": 5,
                        "extra_hours": 0,
                        "date_worked": "2022-03-01"
                    },
                    "2022-03-02": {
                        "work_hours": 6,
                        "pto_hours": 1,
                        "extra_hours": 0,
                        "date_worked": "2022-03-02"
                    },
                    .....
                }
            }
        }


..  http:post:: /api/v1/timesheet/:{employee_id}:

    An endpoint to create a time sheet for an employee for a given date in YYYY-MM-DD format.
    It requires a list of records consisting of work hours, PTO hours, Extra/OT hours, and the date worked.

    :param employee_id: The employee ID of the employee.
    :param time_sheets: The list of hours and the corresponding work dates.
    :status 201: When the employee time sheets are successfully added to the database.
    :status 400: When the request body contains invalid parameters, or one or more employee time sheets already exist for a provided date.

    **Example request**:

    .. sourcecode:: http

        POST /api/v1/timesheet/:{employee_id}: HTTP/1.1
        Content-Type: application/json

        Headers:
        {
            "Authorization": "Bearer <access_token>"
        }
        Body:
        {
            "time_sheets": [
                {
                    "hours_worked": 8,
                    "pto_hours": 0,
                    "extra_hours": 0,
                    "date_worked": "2022-03-01"
                },
                {
                    "hours_worked": 8,
                    "pto_hours": 0,
                    "extra_hours": 2,
                    "date_worked": "2022-03-02"
                },
                .....
            ]
        }

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 201 OK
        Content-Type: application/json

        {
            "status": 201,
            "message": "success",
            "data": {
                "time_sheets": [
                    {
                        "hours_worked": 8,
                        "pto_hours": 0,
                        "extra_hours": 0,
                        "date_worked": "2022-03-01"
                    },
                    {
                        "hours_worked": 8,
                        "pto_hours": 0,
                        "extra_hours": 2,
                        "date_worked": "2022-03-02"
                    },
                    .....
                ]
            }
        }


..  http:put:: /api/v1/timesheet/:{employee_id}:

    An endpoint that updates an individual time sheet of an employee on the given date with new hours.

    :param date_worked: The date of the time sheet to be updated in YYYY-MM-DD format.
    :param work_hours [OPTIONAL]: The Work hours that need to be updated.
    :param pto_hours [OPTIONAL]: The PTO hours that need to be updated.
    :param extra_hours [OPTIONAL]: The Extra/OT hours that need to be updated.
    :status 200: When the employee time sheets are successfully deleted for the given date.
    :status 400: When the request body is invalid, or the time sheet does not exist for the given date.

    **Example request**:

    .. sourcecode:: http

        PUT /api/v1/timesheet/:{employee_id}:

        URL: /api/v1/timesheet/jsmith317
        Headers:
        {
            "Authorization": "Bearer <access_token>"
        }
        Body:
        {
            "date_worked": "2022-03-01",
            "work_hours": 15
        }


   **Example response**:

   .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "status": 200,
            "message": "success",
            "data": {
                "time_sheet": {
                    "work_hours": 15,
                    "pto_hours": 0,
                    "extra_hours": 0,
                    "date_worked": "2022-03-01"
                }
            }
        }


..  http:delete:: /api/v1/timesheet:

    An endpoint that deletes all the time sheets of an employee.

    :param employee_id: The ID of the employee to remove time sheets from.
    :status 200: When the employee time sheets are successfully deleted.
    :status 400: When the request body is invalid, or the employee does not exist.

    **Example request**:

    .. sourcecode:: http

        DELETE /api/v1/timesheet

        URL: /api/v1/timesheet
        Headers:
        {
            "Authorization": "Bearer <access_token>"
        }
        Params:
        {
            "employee_id": "jsmith317"
        }


   **Example response**:

   .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "status": 200,
            "message": "success",
            "data": {}
        }


..  http:delete:: /api/v1/timesheet/:{employee_id}:

    An endpoint that deletes time sheets of an employee on the given dates.

    :param dates_worked: The list of dates of the time sheets to be deleted in YYYY-MM-DD format.
    :status 200: When the employee time sheet is successfully updated for the given date.
    :status 400: When the request body is invalid, or the time sheet does not exist for the given date.

    **Example request**:

    .. sourcecode:: http

        DELETE /api/v1/timesheet/:{employee_id}:

        URL: /api/v1/timesheet/jsmith317
        Headers:
        {
            "Authorization": "Bearer <access_token>"
        }
        Body:
        {
            "dates_worked": ["2022-03-01", "2022-03-02"]
        }


   **Example response**:

   .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "status": 200,
            "message": "success",
            "data": {
                "time_sheets": [
                    {
                        "work_hours": 8,
                        "pto_hours": 5,
                        "extra_hours": 0,
                        "date_worked": "2022-03-01"
                    },
                    {
                        "work_hours": 6,
                        "pto_hours": 1,
                        "extra_hours": 0,
                        "date_worked": "2022-03-02"
                    }
                ]
            }
        }


Implementation Documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: server.web_api.routing.v1.employee_hours_routing
   :members:
   :undoc-members:
   :show-inheritance: