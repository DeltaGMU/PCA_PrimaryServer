"""
This module consists of FastAPI routing for Students.
This handles all the REST API logic for creating, destroying, and updating student-related data.
"""
import time
from datetime import datetime, timedelta

from fastapi import Body, status, HTTPException
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from typing import Dict
from server.lib.utils.student_utils import generate_student_id
from server.web_api.models import ResponseModel
from server.lib.data_classes.student import Student, PydanticStudent, StudentCareHours, PydanticStudentCareHoursCheckIn, PydanticStudentCareHoursCheckOut
from server.lib.service_manager import SharedData

router = InferringRouter()


# pylint: disable=R0201
@cbv(router)
class StudentsRouter:
    """
    The API router responsible for defining endpoints relating to students.
    The defined endpoints allow HTTP requests to conduct childcare-related operations with the student entity.
    """

    @router.get("/api/v1/students", status_code=status.HTTP_200_OK)
    def get_all_students(self):
        """
        An endpoint that retrieves all the students from the database.

        :return: List of all the students in the database.
        :rtype: server.web_api.models.ResponseModel
        """
        all_students = []
        with SharedData().Managers.get_database_manager().make_session() as session:
            employees = session.query(Student).all()
            for row in employees:
                item: Student = row
                all_students.append(item.as_dict())
        return ResponseModel(status.HTTP_200_OK, "success", {"students": all_students})

    @router.post("/api/v1/students/new", status_code=status.HTTP_201_CREATED)
    def create_new_student(self, student: PydanticStudent):
        """
        An endpoint that creates a new student record and adds it to the students' table in the database.

        :param student: The Pydantic Student reference. This means that HTTP requests to this endpoint must include the required fields in the Pydantic Student class.
        :type student: PydanticStudent
        :return: A response model containing the student object that was created and inserted into the database.
        :rtype: server.web_api.models.ResponseModel
        :raises HTTPException: If the request body contains a student first name or last name that is invalid, or the data provided is formatted incorrectly.
        """
        with SharedData().Managers.get_database_manager().make_session() as session:
            student_id = generate_student_id(student.FirstName.strip(), student.LastName.strip())
            if student_id is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The student first name or last name is invalid and cannot be used to create an student ID!")
            try:
                new_student = Student(student_id, student.FirstName, student.LastName)
                session.add(new_student)
                session.commit()
            except IntegrityError as err:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
            created_student = session.query(Student).filter(Student.StudentID == student_id).one()
        return ResponseModel(status.HTTP_201_CREATED, "success", {"student": created_student.as_dict()})

    @router.get("/api/v1/students/count", status_code=status.HTTP_200_OK)
    def get_students_count(self):
        """
        An endpoint that counts the number of students that are registered in the database.

        :return: A response model containing the number of students in the database. The count will be 0 if there are no students registered in the database.
        :rtype: server.web_api.models.ResponseModel
        """
        with SharedData().Managers.get_database_manager().make_session() as session:
            students_count = session.query(Student).count()
        return ResponseModel(status.HTTP_200_OK, "success", {"count": students_count})

    @router.post("/api/v1/students/checkin", status_code=status.HTTP_201_CREATED)
    def check_in_student(self, student_checkin: PydanticStudentCareHoursCheckIn):
        """
        An endpoint that checks-in a student into the before-care or after-care service and records the time of check-in.
        Any student checked into before-care is automatically checked out at the end of the before-care service.
        Any student checked into after-care can be checked out at any time after checking in.
        Failure to check out a student from after-care will result in the automatic check-out of the student at the end of after-care.

        :param student_checkin: The Pydantic StudentCareHoursCheckIn reference. This means that HTTP requests to this endpoint must include the required fields in the Pydantic StudentCareHoursCheckIn class.
        :type student_checkin: PydanticStudentCareHoursCheckIn
        :return: A response model containing information regarding the student and the check-in time and date that has been registered in the database.
        :rtype: server.web_api.models.ResponseModel
        :raises HTTPException: If the data provided in the request body is invalid, or the student is already checked in to the care service for the provided date.
        """
        with SharedData().Managers.get_database_manager().make_session() as session:
            student_care = session.query(StudentCareHours).filter(
                StudentCareHours.StudentID == student_checkin.StudentID,
                StudentCareHours.CareDate == student_checkin.CareDate,
                StudentCareHours.CareType == student_checkin.CareType
            ).first()
            if student_care is None:
                try:
                    new_student_care_hours = StudentCareHours(student_checkin.StudentID,
                                                              student_checkin.CareDate,
                                                              student_checkin.CareType,
                                                              datetime.strptime(time.strftime('%H:%M'), '%H:%M') if student_checkin.CheckInTime is None else datetime.strptime(student_checkin.CheckInTime, '%H:%M'),
                                                              datetime.strptime((datetime.now() + timedelta(hours=3)).strftime('%H:%M'), '%H:%M'))
                    session.add(new_student_care_hours)
                    session.commit()
                except IntegrityError as err:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=f"This student has already checked-in for {'after' if student_care.CareType else 'before'}-care "
                                           f"for the provided date: {student_checkin.CareDate} at {student_checkin.CheckInTime}")
        return ResponseModel(status.HTTP_201_CREATED, "success", {"check-in": new_student_care_hours.as_dict()})

    @router.post("/api/v1/students/checkout", status_code=status.HTTP_200_OK)
    def check_out_student(self, student_checkout: PydanticStudentCareHoursCheckOut):
        """
        Not Implemented!
        
        :param student_checkout: Not Implemented!
        :type student_checkout: Not Implemented!
        :return: Not Implemented!
        :rtype: Not Implemented!
        """
        with SharedData().Managers.get_database_manager().make_session() as session:
            pass
