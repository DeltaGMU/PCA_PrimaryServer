"""
This module consists of FastAPI routing for Students.
This handles all the REST API logic for creating, destroying, and updating student-related data.
"""
import time
from datetime import datetime, timedelta
from fastapi import Body, status, HTTPException, Depends
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from config import ENV_SETTINGS
from server.lib.database_access.student_interface import create_student, get_student_by_id, get_student_contact_info, update_students, update_student, remove_students, get_student_grade
from server.web_api.models import ResponseModel
from server.lib.data_classes.student import Student, PydanticStudentRegistration, PydanticMultipleStudentsUpdate, PydanticStudentUpdate, PydanticStudentsRemoval
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

            :param pyd_student: The new student's first name, last name, carpool number, parent full name, parent primary email, student grade, and optional parameters like parent secondary email and enabling email notifications.
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
        @router.get(ENV_SETTINGS.API_ROUTES.Students.one_student, status_code=status.HTTP_200_OK)
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
            student = await get_student_by_id(student_id.strip(), session)
            if student is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The student could not be retrieved.")
            full_student_information = student.as_dict()
            return ResponseModel(status.HTTP_200_OK, "success", {"student": full_student_information})

    class Update:
        @staticmethod
        @router.put(ENV_SETTINGS.API_ROUTES.Students.students, status_code=status.HTTP_201_CREATED)
        async def update_multiple_students(multi_student_update: PydanticMultipleStudentsUpdate, token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
            """
            An endpoint that updates multiple students from the database from the provided employee information and employee ID.

            :param multi_student_update: A dictionary that consists of pairs of student IDs and update information as per the ``PydanticStudentUpdate`` parameters.
            :type multi_student_update: PydanticMultipleStudentsUpdate, required
            :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
            :type token: str, required
            :param session: The database session to use to update multiple student data.
            :type session: sqlalchemy.orm.session, optional
            :return: A response model containing the multiple student updated data in the database.
            :rtype: server.web_api.models.ResponseModel
            :raises HTTPException: If the authentication token is invalid or the students could not be updated.
            """
            if not await token_is_valid(token, ["administrator"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            updated_students = await update_students(multi_student_update.student_updates, session)
            if updated_students is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more provided parameters were invalid!")
            return ResponseModel(status.HTTP_200_OK, "success", {"students": [student.as_dict() for student in updated_students]})

        @staticmethod
        @router.put(ENV_SETTINGS.API_ROUTES.Students.one_student, status_code=status.HTTP_201_CREATED)
        async def update_one_student(student_id: str, student_update: PydanticStudentUpdate, token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
            """
            An endpoint that updates a single student from the database from the provided student information and student ID.

            :param student_id: The ID of the student.
            :type student_id: str, required
            :param student_update: The ID of the student and any other student information that needs to be updated.
            :type student_update: PydanticStudentUpdate, required
            :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
            :type token: str, required
            :param session: The database session to use to update the student data.
            :type session: sqlalchemy.orm.session, optional
            :return: A response model containing the student updated in the database.
            :rtype: server.web_api.models.ResponseModel
            :raises HTTPException: If the authentication token is invalid or the student could not be updated.
            """
            if not await token_is_valid(token, ["administrator"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            if student_id is None or not isinstance(student_id, str):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="The student ID must be a valid string!")
            updated_student = await update_student(student_id.strip(), student_update, session)
            if updated_student is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more provided parameters were invalid!")
            return ResponseModel(status.HTTP_200_OK, "success", {"student": updated_student.as_dict()})

    class Delete:
        @staticmethod
        @router.delete(ENV_SETTINGS.API_ROUTES.Students.students, status_code=status.HTTP_200_OK)
        async def delete_students(student_ids: PydanticStudentsRemoval, token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
            """
            An endpoint to remove multiple student records from the student's table in the database.
            Removal of multiple students using this endpoint will permanently delete the student records from the database
            and all records related to the student records in other tables through a cascading delete.
            To remove multiple student records, the student IDs must be provided in a list.

            :param student_ids: A list of IDs of students that needs to be deleted.
            :type student_ids: PydanticStudentsRemoval, required
            :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
            :type token: str, required
            :param session: The database session to use to delete the student record.
            :type session: sqlalchemy.orm.session, optional
            :return: A response model containing the student object that was deleted from the database.
            :rtype: server.web_api.models.ResponseModel
            :raises HTTPException: If the provided request body contains an invalid student ID, or if the student does not exist in the database.
            """
            if not await token_is_valid(token, ["administrator"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            removed_students = await remove_students(student_ids, session)
            return ResponseModel(status.HTTP_200_OK, "success", {"students": [student.as_dict() for student in removed_students]})

        @staticmethod
        @router.delete(ENV_SETTINGS.API_ROUTES.Students.one_student, status_code=status.HTTP_200_OK)
        async def delete_student(student_id: str, token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
            """
            An endpoint to remove a student record from the student's table in the database.
            Removal of a student using this endpoint will permanently delete the student record from the database
            and all records related to the student record in other tables through a cascading delete.

            :param student_id: The ID of the student that needs to be deleted.
            :type student_id: str, required
            :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
            :type token: str, required
            :param session: The database session to use to delete the student record.
            :type session: sqlalchemy.orm.session, optional
            :return: A response model containing the student object that was deleted from the database.
            :rtype: server.web_api.models.ResponseModel
            :raises HTTPException: If the provided request body contains an invalid student ID, or if the student does not exist in the database.
            """
            if not await token_is_valid(token, ["administrator"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            if student_id is None or not isinstance(student_id, str):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="The employee ID must be a valid string!")
            removed_students = await remove_students(student_id.strip(), session)
            return ResponseModel(status.HTTP_200_OK, "success", {"employee": [student.as_dict() for student in removed_students]})
