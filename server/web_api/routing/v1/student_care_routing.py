"""
This module consists of FastAPI routing for Students.
This handles all the REST API logic for creating, destroying, and updating student-related data.
"""
from fastapi import Body, status, HTTPException, Depends
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from config import ENV_SETTINGS
from server.lib.database_access.student_care_interface import check_in_student, check_out_student
from server.web_api.models import ResponseModel
from server.lib.data_classes.student_care_hours import PydanticStudentCareHoursCheckIn, PydanticStudentCareHoursCheckOut
from server.lib.database_manager import get_db_session

router = InferringRouter()


# pylint: disable=R0201
@cbv(router)
class StudentCareRouter:
    """
    The API router responsible for defining endpoints relating to students.
    The defined endpoints allow HTTP requests to conduct create, read, update, and delete tasks on student records.
    """
    class Service:
        @staticmethod
        @router.post(ENV_SETTINGS.API_ROUTES.StudentCare.check_in, status_code=status.HTTP_201_CREATED)
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
        @router.post(ENV_SETTINGS.API_ROUTES.StudentCare.check_out, status_code=status.HTTP_200_OK)
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
