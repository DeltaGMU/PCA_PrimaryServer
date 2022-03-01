Students API - WORK IN PROGRESS
==================================

This page highlights the different endpoints that are available
to the web interface to interact with student data and before-care/after-care services data.

Usage
~~~~~~

.. http:get:: /api/v1/students

   An endpoint that retrieves all the students from the database and formats it into a list.

   :status 200: When the list of students is successfully retrieved from the database.

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


.. http:get:: /api/v1/students/count

   An endpoint that counts the number of students registered in the database and returns it in the response.

   :status 200: When the total number of students is successfully retrieved from the database.

   **Example request**:

   .. sourcecode:: http

      GET /api/v1/students/count HTTP/1.1

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "status": 200,
        "message": "success",
        "data": {
            "count": 2
        }
      }


.. http:post:: /api/v1/students/new

   An endpoint that creates a new student in the database given a valid first and last name.

   :param first_name: The first name of the new student.
   :param last_name: The last name of the new student.
   :status 201: When the new student is successfully added to the database.
   :status 400: When the first or last name of the new student is invalid, or the student already exists in the database

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


.. http:post:: /api/v1/students/checkin

   An endpoint that creates a new student in the database given a valid first and last name.
   KNOWN ERRORS: Currently a successful student check in returns a status 500 error even though the student was successfully checked in.

   :param student_id: The student ID of the student.
   :param check_in_date: The date that the student is checked in to the care service.
   :param care_type: The type of care the student is registered to indicated by 'false' for before-care, and 'true' for after-care.
   :status 200: When the student is successfully checked in to the chosen service.
   :status 400: When the request body contains invalid parameters, or the student is already checked in to the chosen service for the day.

   **Example request**:

   .. sourcecode:: http

      POST /api/v1/students HTTP/1.1
      Content-Type: application/json

      {
        "student_id": "jjerome4",
        "check_in_date": "2022-02-20",
        "care_type": false
      }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "status": 200,
        "message": "success",
        "data": {
            "student": {
                "student_id": "jjerome5",
                "first_name": "Jason",
                "last_name": "Jerome",
                "check_in_date": "2022-02-20",
                "check_in_time": "20:46:14",
                "check_out_time": null,
                "care_type": false,
                "entry_created": "2022-02-20T20:46:14"
            }
        }
      }

Implementation Documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: server.web_api.routing.v1.students.routing
   :members:
   :undoc-members:
   :show-inheritance:
