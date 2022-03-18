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
from server.lib.database_access.student_interface import create_student, get_student_by_id, get_student_contact_info
from server.web_api.models import ResponseModel
from server.lib.data_classes.student import Student, PydanticStudentRegistration
from server.lib.data_classes.student_care_hours import StudentCareHours, PydanticStudentCareHoursCheckIn, PydanticStudentCareHoursCheckOut
from server.lib.database_manager import get_db_session
from server.web_api.web_security import token_is_valid, oauth_scheme

router = InferringRouter()


# pylint: disable=R0201
@cbv(router)
class StudentsRouter:
    """
    The API router responsible for defining endpoints relating to students.
    The defined endpoints allow HTTP requests to conduct create, read, update, and delete tasks on student records.
    """

    class Create:
        @staticmethod
        @router.post(ENV_SETTINGS.API_ROUTES.Students.students, status_code=status.HTTP_201_CREATED)
        async def create_new_student(pyd_student: PydanticStudentRegistration, token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
            """
            An endpoint that creates a new student record and adds it to the students' table in the database.

            :param pyd_student: The new student's first name, last name, carpool number, parent full name, parent primary email, and optional parameters like parent secondary email and enabling email notifications.
            :type pyd_student: PydanticStudentRegistration, required
            :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
            :type token: str, required
            :param session: The database session to use to create a new student record in the database.
            :type session: sqlalchemy.orm.session, optional
            :return: A response model containing the student object that was created and inserted into the database.
            :rtype: server.web_api.models.ResponseModel
            :raises HTTPException: If the request body contains any invalid parameters, or the data provided is formatted incorrectly.
            """
            if not await token_is_valid(token, ["administrator"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            created_student = await create_student(pyd_student, session)
            return ResponseModel(status.HTTP_201_CREATED, "success", {"student": created_student})

    class Read:
        @staticmethod
        @router.get(ENV_SETTINGS.API_ROUTES.Students.count, status_code=status.HTTP_200_OK)
        async def read_students_count(token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
            """
            An endpoint that counts the number of students that are registered in the database.

            :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
            :type token: str, required
            :param session: The database session to use to retrieve the number of student records.
            :type session: sqlalchemy.orm.session, optional
            :return: A response model containing the number of students in the database. The count will be 0 if there are no students registered in the database.
            :rtype: server.web_api.models.ResponseModel
            """
            if not await token_is_valid(token, ["administrator"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            students_count = session.query(Student).count()
            return ResponseModel(status.HTTP_200_OK, "success", {"count": students_count})

        @staticmethod
        @router.get(ENV_SETTINGS.API_ROUTES.Students.students, status_code=status.HTTP_200_OK)
        async def read_all_students(token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
            """
            An endpoint that retrieves all the students from the database.

            :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
            :type token: str, required
            :param session: The database session to use to retrieve all student records.
            :type session: sqlalchemy.orm.session, optional
            :return: List of all the students in the database.
            :rtype: server.web_api.models.ResponseModel
            """
            if not await token_is_valid(token, ["administrator"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            all_students = []
            employees = session.query(Student).all()
            for row in employees:
                item: Student = row
                all_students.append(item.as_dict())
            return ResponseModel(status.HTTP_200_OK, "success", {"students": all_students})

        @staticmethod
        @router.get(ENV_SETTINGS.API_ROUTES.Students.student, status_code=status.HTTP_200_OK)
        async def read_one_student(student_id: str, token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
            """
            An endpoint that retrieves a single student from the database.

            :param student_id: The ID of the student.
            :type student_id: str, required
            :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
            :type token: str, required
            :param session: The database session to use to retrieve a single student record.
            :type session: sqlalchemy.orm.session, optional
            :return: A single student from the database.
            :rtype: server.web_api.models.ResponseModel
            """
            if not await token_is_valid(token, ["employee"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            if student_id is None or not isinstance(student_id, str):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The student ID must be a valid string!")
            student = await get_student_by_id(student_id.strip())
            if student is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The student could not be retrieved.")
            full_student_information = student.as_dict()
            full_student_information.update((await get_student_contact_info(student)).as_dict())
            return ResponseModel(status.HTTP_200_OK, "success", {"student": full_student_information})

    class Update:
        pass

    class Delete:
        pass

    @staticmethod
    @router.post("/api/v1/students/checkin", status_code=status.HTTP_201_CREATED)
    def check_in_student(pyd_student_checkin: PydanticStudentCareHoursCheckIn, session=Depends(get_db_session)):
        """
        An endpoint that checks-in a student into the before-care or after-care service and records the time of check-in.
        Any student checked into before-care is automatically checked out at the end of the before-care service.
        Any student checked into after-care can be checked out at any time after checking in.
        Failure to check out a student from after-care will result in the automatic check-out of the student at the end of after-care.

        :param pyd_student_checkin: The Pydantic StudentCareHoursCheckIn reference. This means that HTTP requests to this endpoint must include the required fields in the Pydantic StudentCareHoursCheckIn class.
        :type pyd_student_checkin: PydanticStudentCareHoursCheckIn
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
                new_student_care_hours = StudentCareHours(pyd_student_checkin.student_id,
                                                          pyd_student_checkin.check_in_date,
                                                          pyd_student_checkin.care_type,
                                                          datetime.strptime(time.strftime('%H:%M'), '%H:%M') if pyd_student_checkin.check_in_time is None else datetime.strptime(pyd_student_checkin.check_in_time, '%H:%M'),
                                                          datetime.strptime((datetime.now() + timedelta(hours=3)).strftime('%H:%M'), '%H:%M'))
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
        :return: Not Implemented!
        :rtype: Not Implemented!
        """
        pass
