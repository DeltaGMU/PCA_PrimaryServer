"""
This module consists of FastAPI routing for Students.
This handles all the REST API logic for creating, destroying, and updating student-related data.
"""

from fastapi import Body, status, HTTPException
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from typing import Dict
from src.lib.utils.student_utils import generate_student_id
from src.web_api.models import ResponseModel
from src.lib.data_classes.student import Student, PydanticStudent, StudentCareHours, PydanticStudentCareHours
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
        return ResponseModel(status.HTTP_201_CREATED, "success", {"student": created_student})

    @router.get("/api/v1/students/count", status_code=status.HTTP_200_OK)
    def get_students_count(self):
        with SharedData().Managers.get_session_manager().make_session() as session:
            students_count = session.query(Student).count()
        return ResponseModel(status.HTTP_200_OK, "success", {"count": students_count})
