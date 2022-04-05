"""
This module consists of FastAPI routing for Reports.
This handles all the REST API logic for creating reports for students and employees.
"""
from fastapi import status, HTTPException, Depends
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from server.web_api.api_routes import API_ROUTES
from server.lib.data_classes.student_grade import PydanticStudentGrade
from server.lib.database_access.student_grades_interface import create_student_grade, remove_student_grade, retrieve_all_grades, retrieve_one_grade
from server.lib.database_manager import get_db_session
from server.web_api.web_security import token_is_valid, oauth_scheme
from server.web_api.models import ResponseModel

router = InferringRouter()


# pylint: disable=R0201
@cbv(router)
class StudentGradesRouter:
    """
    The API router responsible for defining endpoints relating to student grades.
    The defined endpoints allow HTTP requests to conduct create, read, update, and delete tasks on student grade records.
    """
    class Create:
        @staticmethod
        @router.post(API_ROUTES.StudentGrade.grades, status_code=status.HTTP_201_CREATED)
        async def create_student_grade(student_grade: PydanticStudentGrade, token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
            """
            An endpoint that creates a student grade in the database system.

            :param student_grade: The name of the student grade that should be added.
            :type student_grade: str, required
            :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
            :type token: str, required
            :param session: The database session to use to create a new student record in the database.
            :type session: sqlalchemy.orm.session, optional
            :return: A response model containing the file path of the employee time sheet report that was created.
            :rtype: server.web_api.models.ResponseModel
            :raises HTTPException: If the request body contains any invalid parameters, or the data provided is formatted incorrectly.
            """
            if not await token_is_valid(token, ["administrator"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            new_student_grade = await create_student_grade(student_grade, session)
            return ResponseModel(status.HTTP_200_OK, "success", {"grade": new_student_grade.as_dict()})

    class Read:
        @staticmethod
        @router.get(API_ROUTES.StudentGrade.grades, status_code=status.HTTP_200_OK)
        async def get_all_student_grades(token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
            """
            An endpoint that retrieves all student grades in the database system.

            :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
            :type token: str, required
            :param session: The database session to use to retrieve all student grade records in the database.
            :type session: sqlalchemy.orm.session, optional
            :return: A response model containing the list of all the student grades that was created.
            :rtype: server.web_api.models.ResponseModel
            :raises HTTPException: If the request body contains any invalid parameters, or the data provided is formatted incorrectly.
            """
            if not await token_is_valid(token, ["employee"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            student_grades = await retrieve_all_grades(session)
            return ResponseModel(status.HTTP_200_OK, "success", {"grades": [student_grade.as_dict() for student_grade in student_grades]})

        @staticmethod
        @router.get(API_ROUTES.StudentGrade.one_grade, status_code=status.HTTP_200_OK)
        async def get_one_student_grade(grade_name: str, token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
            """
            An endpoint that retrieves one student grade in the database system.

            :param grade_name: The student grade to be retrieved.
            :type grade_name: PydanticStudentGrade, required
            :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
            :type token: str, required
            :param session: The database session to use to retrieve one student grade record in the database.
            :type session: sqlalchemy.orm.session, optional
            :return: A response model containing the student grade that was retrieved.
            :rtype: server.web_api.models.ResponseModel
            :raises HTTPException: If the request body contains any invalid parameters, or the data provided is formatted incorrectly.
            """
            if not await token_is_valid(token, ["administrator"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            grade = await retrieve_one_grade(grade_name, session)
            return ResponseModel(status.HTTP_200_OK, "success", {"grade": grade.as_detail_dict()})

    class Delete:
        @staticmethod
        @router.post(API_ROUTES.StudentGrade.remove_grade, status_code=status.HTTP_200_OK)
        async def delete_student_grade(student_grade: PydanticStudentGrade, token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
            """
            An endpoint that deletes an employee time sheet report provided the starting reporting period as a year and month in the YYYY-MM format.

            :param student_grade: The student grade to be deleted.
            :type student_grade: str, required
            :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
            :type token: str, required
            :param session: The database session to use to delete a student grade record in the database.
            :type session: sqlalchemy.orm.session, optional
            :return: A response model containing the name of the deleted student grade.
            :rtype: server.web_api.models.ResponseModel
            :raises HTTPException: If the request body contains any invalid parameters, or the data provided is formatted incorrectly.
            """
            if not await token_is_valid(token, ["administrator"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            removed_grade = await remove_student_grade(student_grade, session)
            return ResponseModel(status.HTTP_200_OK, "success", {"grade": removed_grade.as_dict()})
