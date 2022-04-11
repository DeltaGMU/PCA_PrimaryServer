"""
This module consists of FastAPI routing for Students.
This handles all the REST API logic for creating, destroying, and updating student-related data.
"""
from fastapi import status, HTTPException, Depends
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from server.web_api.api_routes import API_ROUTES
from server.lib.database_controllers.student_interface import get_student_by_id
from server.lib.database_controllers.student_care_interface import check_in_student, check_out_student, get_one_student_care, \
    get_care_students_by_grade, get_student_care_records, delete_student_care_records, get_total_student_care_for_period
from server.web_api.models import ResponseModel
from server.lib.data_models.student_care_hours import PydanticStudentCareHoursCheckIn, PydanticStudentCareHoursCheckOut, \
    PydanticRetrieveCareStudentsByGrade, PydanticRetrieveStudentCareRecord, PydanticDeleteStudentCareRecord, PydanticRetrieveTotalHoursByGrade
from server.lib.database_manager import get_db_session
from server.web_api.web_security import token_is_valid, oauth_scheme

router = InferringRouter()


# pylint: disable=R0201
@cbv(router)
class StudentCareRouter:
    """
    The API router responsible for defining endpoints relating to students.
    The defined endpoints allow HTTP requests to conduct create, read, update, and delete tasks on student records.
    """
    class Read:
        @staticmethod
        @router.get(API_ROUTES.StudentCareKiosk.one_student_info, status_code=status.HTTP_200_OK)
        async def read_one_student_limited(student_id: str, session=Depends(get_db_session)):
            """
            An endpoint that retrieves limited information about a single student from the database.

            :param student_id: The ID of the student.
            :type student_id: str, required
            :param session: The database session to use to retrieve a single student record.
            :type session: sqlalchemy.orm.session, optional
            :return: A single student from the database.
            :rtype: server.web_api.models.ResponseModel
            """
            if student_id is None or not isinstance(student_id, str):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The student ID must be a valid string!")
            student = await get_student_by_id(student_id.strip(), session)
            if student is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The student could not be retrieved.")
            full_student_information = student.as_limited_dict()
            return ResponseModel(status.HTTP_200_OK, "success", {"student": full_student_information})

        @staticmethod
        @router.get(API_ROUTES.StudentCareKiosk.one_student_care, status_code=status.HTTP_200_OK)
        async def read_one_student_care(student_id: str, care_date: str, session=Depends(get_db_session)):
            """
            An endpoint that retrieves information about a single student's student care from the database.

            :param student_id: The ID of the student.
            :type student_id: str, required
            :param care_date: The date of the care service provided in YYYY-MM-DD format.
            :type care_date: str, required
            :param session: The database session to use to retrieve a single student record.
            :type session: sqlalchemy.orm.session, optional
            :return: A single student from the database.
            :rtype: server.web_api.models.ResponseModel
            """
            if student_id is None or not isinstance(student_id, str):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The student ID must be a valid string!")
            student_care = await get_one_student_care(student_id.strip(), care_date.strip(), session)
            if student_care is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The student care information not be retrieved.")
            return ResponseModel(status.HTTP_200_OK, "success", {"care": student_care})

        @staticmethod
        @router.post(API_ROUTES.StudentCare.care, status_code=status.HTTP_200_OK)
        async def read_students_by_grade(pyd_care_students: PydanticRetrieveCareStudentsByGrade, token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
            """
            An endpoint that returns a list of the students that are participating in before/after-care for the provided date in the provided student grade.
            If a student has already participated in student care on the provided day, a flag is set on the student's information in the response.

            :param pyd_care_students: The student grade, care type, and care date.
            :type pyd_care_students: PydanticRetrieveStudentsByCareDate, required
            :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
            :type token: str, required
            :param session: The database session to use to identify students that used the care service.
            :type session: sqlalchemy.orm.session, optional
            :return: A response model containing the list of students that used the care service.
            :rtype: server.web_api.models.ResponseModel
            :raises HTTPException: If the data provided in the request body is invalid, or the student is already checked in to the care service for the provided date.
            """
            if not await token_is_valid(token, ["employee"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            list_of_student_care = await get_care_students_by_grade(pyd_care_students, session)
            return ResponseModel(status.HTTP_200_OK, "success", {"students": list_of_student_care})

        @staticmethod
        @router.post(API_ROUTES.StudentCare.total_hours_records, status_code=status.HTTP_200_OK)
        async def read_students_total_care(pyd_care_students: PydanticRetrieveTotalHoursByGrade, token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
            """
            An endpoint that returns a list of the students with their accumulated before-care and after-care hours for the provided reporting period in the provided student grade.

            :param pyd_care_students: The student grade, start date and end date.
            :type pyd_care_students: PydanticRetrieveStudentsByCareDate, required
            :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
            :type token: str, required
            :param session: The database session to use to identify students that used the care service.
            :type session: sqlalchemy.orm.session, optional
            :return: A response model containing the list of students that used the care service.
            :rtype: server.web_api.models.ResponseModel
            :raises HTTPException: If the data provided in the request body is invalid, or the student is already checked in to the care service for the provided date.
            """
            if not await token_is_valid(token, ["administrator"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            list_of_student_care = await get_total_student_care_for_period(pyd_care_students.start_date, pyd_care_students.end_date, pyd_care_students.grade, session)
            return ResponseModel(status.HTTP_200_OK, "success", {"students": list_of_student_care})

        @staticmethod
        @router.post(API_ROUTES.StudentCare.records, status_code=status.HTTP_200_OK)
        async def read_student_care_records(pyd_care_students: PydanticRetrieveStudentCareRecord, token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
            """
            An endpoint that returns a list of the student records from the provided date range.

            :param pyd_care_students: The student ID, care start date, and care end date.
            :type pyd_care_students: PydanticRetrieveStudentCareRecord, required
            :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
            :type token: str, required
            :param session: The database session to use to collect student care records from the database.
            :type session: sqlalchemy.orm.session, optional
            :return: A response model containing the student care records.
            :rtype: server.web_api.models.ResponseModel
            :raises HTTPException: If the data provided in the request body is invalid.
            """
            if not await token_is_valid(token, ["administrator"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            list_of_records = await get_student_care_records(pyd_care_students, session)
            return ResponseModel(status.HTTP_200_OK, "success", {"records": list_of_records})

    class Delete:
        @staticmethod
        @router.post(API_ROUTES.StudentCare.remove_records, status_code=status.HTTP_200_OK)
        async def delete_student_care_record(pyd_care_students: PydanticDeleteStudentCareRecord, token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
            """
            An endpoint that deletes a student care record for a specific student on the provided date.

            :param pyd_care_students: The student ID, care date, and optionally the care type.
            :type pyd_care_students: PydanticDeleteStudentCareRecord, required
            :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
            :type token: str, required
            :param session: The database session to use to delete student care records from the database.
            :type session: sqlalchemy.orm.session, optional
            :return: A response model containing the success message.
            :rtype: server.web_api.models.ResponseModel
            :raises HTTPException: If the data provided in the request body is invalid.
            """
            if not await token_is_valid(token, ["administrator"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            await delete_student_care_records(pyd_care_students, session)
            return ResponseModel(status.HTTP_200_OK, "success")

    class Service:
        @staticmethod
        @router.post(API_ROUTES.StudentCare.check_in, status_code=status.HTTP_201_CREATED)
        async def check_in_student(pyd_student_checkin: PydanticStudentCareHoursCheckIn, session=Depends(get_db_session)):
            """
            An endpoint that checks-in a student into the before-care or after-care service and records the time of check-in.
            Any student checked into before-care is automatically checked out at the end of the before-care service.
            Any student checked into after-care can be checked out at any time after checking in.
            Failure to check out a student from after-care will result in the automatic check-out of the student at the end of after-care.

            :param pyd_student_checkin: The Pydantic StudentCareHoursCheckIn reference. This means that HTTP requests to this endpoint must include the required fields in the Pydantic StudentCareHoursCheckIn class.
            :type pyd_student_checkin: PydanticStudentCareHoursCheckIn
            :param session: The database session to use to check in a student.
            :type session: sqlalchemy.orm.session, optional
            :return: A response model containing information regarding the student and the check-in time and date that has been registered in the database.
            :rtype: server.web_api.models.ResponseModel
            :raises HTTPException: If the data provided in the request body is invalid, or the student is already checked in to the care service for the provided date.
            """
            checked_in_student = await check_in_student(pyd_student_checkin, session)
            return ResponseModel(status.HTTP_201_CREATED, "success", {"check-in": checked_in_student.as_dict()})

        @staticmethod
        @router.post(API_ROUTES.StudentCare.check_out, status_code=status.HTTP_200_OK)
        async def check_out_student(pyd_student_checkout: PydanticStudentCareHoursCheckOut, session=Depends(get_db_session)):
            """
            An endpoint that checks-out a student from the before-care or after-care service and records the time of check-out.
            Students checked into before-care are automatically checked out at the end of the before-care service.
            Any student checked into after-care can be checked out at any time after checking in.
            Failure to check out a student from after-care will result in the automatic check-out of the student at the end of after-care.

            :param pyd_student_checkout: The Pydantic StudentCareHoursCheckOut reference. This means that HTTP requests to this endpoint must include the required fields in the Pydantic StudentCareHoursCheckOut class.
            :type pyd_student_checkout: StudentCareHoursCheckOut, required
            :param session: The database session to use to check out a student.
            :type session: sqlalchemy.orm.session, optional
            :return: A response model containing information regarding the student and the check-out time and date that has been registered in the database.
            :rtype: server.web_api.models.ResponseModel
            :raises HTTPException: If the data provided in the request body is invalid, or the student is already checked out of the care service for the provided date.
            """
            checked_out_student = await check_out_student(pyd_student_checkout, session)
            return ResponseModel(status.HTTP_200_OK, "success", {"check-out": checked_out_student.as_dict()})
