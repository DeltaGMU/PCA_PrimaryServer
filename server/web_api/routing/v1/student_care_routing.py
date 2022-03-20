"""
This module consists of FastAPI routing for Students.
This handles all the REST API logic for creating, destroying, and updating student-related data.
"""
import time
from datetime import datetime, timedelta
from fastapi import Body, status, HTTPException, Depends
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from sqlalchemy.exc import IntegrityError
from config import ENV_SETTINGS
from server.web_api.models import ResponseModel
from server.lib.data_classes.student_care_hours import StudentCareHours, PydanticStudentCareHoursCheckIn, PydanticStudentCareHoursCheckOut
from server.lib.database_manager import get_db_session

router = InferringRouter()


# pylint: disable=R0201
@cbv(router)
class StudentCareRouter:
    """
    The API router responsible for defining endpoints relating to students.
    The defined endpoints allow HTTP requests to conduct create, read, update, and delete tasks on student records.
    """

    @staticmethod
    @router.post(ENV_SETTINGS.API_ROUTES.StudentCare.check_in, status_code=status.HTTP_201_CREATED)
    def check_in_student(pyd_student_checkin: PydanticStudentCareHoursCheckIn, session=Depends(get_db_session)):
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
        student_care = session.query(StudentCareHours).filter(
            StudentCareHours.StudentID == pyd_student_checkin.student_id,
            StudentCareHours.CareDate == pyd_student_checkin.check_in_date,
            StudentCareHours.CareType == pyd_student_checkin.care_type
        ).first()
        if student_care is None:
            try:
                check_in_time = datetime.strptime(time.strftime('%H:%M'), '%H:%M') if pyd_student_checkin.check_in_time is None else datetime.strptime(pyd_student_checkin.check_in_time, '%H:%M')
                check_out_time = datetime.strptime(ENV_SETTINGS.student_before_care_check_out_time if not pyd_student_checkin.care_type else ENV_SETTINGS.student_after_care_check_out_time, '%H:%M')
                print(check_in_time)
                print(check_out_time)
                new_student_care_hours = StudentCareHours(
                    pyd_student_checkin.student_id,
                    pyd_student_checkin.check_in_date,
                    pyd_student_checkin.care_type,
                    check_in_time,
                    check_out_time
                )
                # datetime.strptime((datetime.now() + timedelta(hours=3)).strftime('%H:%M'), '%H:%M'))
                session.add(new_student_care_hours)
                session.commit()
            except IntegrityError as err:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"This student has already checked-in for {'after' if student_care.CareType else 'before'}-care "
                                       f"for the provided date: {pyd_student_checkin.check_in_date} at {pyd_student_checkin.check_in_time}")
        return ResponseModel(status.HTTP_201_CREATED, "success", {"check-in": new_student_care_hours.as_dict()})

    @staticmethod
    @router.post("/api/v1/students/checkout", status_code=status.HTTP_200_OK)
    def check_out_student(student_checkout: PydanticStudentCareHoursCheckOut, session=Depends(get_db_session)):
        """
        Not Implemented!

        :param student_checkout: Not Implemented!
        :type student_checkout: Not Implemented!
        :param session: The database session to use to check out a student.
        :type session: sqlalchemy.orm.session, optional
        :return: Not Implemented!
        :rtype: Not Implemented!
        """
        pass
