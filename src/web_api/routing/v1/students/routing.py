"""
This module consists of FastAPI routing for Students.
This handles all the REST API logic for creating, destroying, and updating student-related data.
"""
from datetime import datetime

from fastapi import Body, status, HTTPException
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from typing import Dict
from src.lib.utils.student_utils import generate_student_id
from src.web_api.models import ResponseModel
from src.lib.data_classes.student import Student, PydanticStudent, StudentCareHours, PydanticStudentCareHoursCheckIn, PydanticStudentCareHoursCheckOut
from src.lib.service_manager import SharedData

router = InferringRouter()


# pylint: disable=R0201
@cbv(router)
class StudentsRouter:
    """
    Router class for employees api.
    """

    @router.get("/api/v1/students", status_code=status.HTTP_200_OK)
    def get_all_students(self):
        """
        Retrieves all the students from the database.
        :return: list of all students in the database
        :rtype: ResponseModel
        """
        all_students = []
        with SharedData().Managers.get_session_manager().make_session() as session:
            employees = session.query(Student).all()
            for row in employees:
                item: Student = row
                all_students.append(item.as_dict())
        return ResponseModel(status.HTTP_200_OK, "success", {"students": all_students})

    @router.post("/api/v1/students/new", status_code=status.HTTP_201_CREATED)
    def create_new_student(self, student: PydanticStudent):
        """
        Creates a new student entity and adds it to the students' table in the database.
        :param student: pydantic student class
        :type student: PydanticStudent
        :return: created student
        :rtype: ResponseModel
        """
        with SharedData().Managers.get_session_manager().make_session() as session:
            student_id = generate_student_id(student.FirstName.strip(), student.LastName.strip())
            try:
                new_student = Student(student_id, student.FirstName, student.LastName, student.StudentEnabled)
                session.add(new_student)
                session.commit()
            except IntegrityError as err:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
            created_student = session.query(Student).filter(Student.StudentID == student_id).one()
        return ResponseModel(status.HTTP_201_CREATED, "success", {"student": created_student.as_dict()})

    @router.get("/api/v1/students/count", status_code=status.HTTP_200_OK)
    def get_students_count(self):
        with SharedData().Managers.get_session_manager().make_session() as session:
            students_count = session.query(Student).count()
        return ResponseModel(status.HTTP_200_OK, "success", {"count": students_count})

    @router.post("/api/v1/students/checkin", status_code=status.HTTP_201_CREATED)
    def check_in_student(self, student_checkin: PydanticStudentCareHoursCheckIn):
        with SharedData().Managers.get_session_manager().make_session() as session:
            student_care = session.query(StudentCareHours).filter(
                StudentCareHours.StudentID == student_checkin.StudentID,
                StudentCareHours.CareDate == student_checkin.CareDate,
                StudentCareHours.CareType == student_checkin.CareType
            ).first()
            if student_care is None:
                try:
                    new_student_care_hours = StudentCareHours(student_checkin.StudentID, student_checkin.CareDate,
                                                              student_checkin.CareType, None if student_checkin.CheckInTime is None else datetime.strptime(student_checkin.CheckInTime, '%H:%M'))
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
        with SharedData().Managers.get_session_manager().make_session() as session:
            pass
