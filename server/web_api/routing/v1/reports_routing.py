"""
This module consists of FastAPI routing for Reports.
This handles all the REST API logic for creating reports for students and employees.
"""
from fastapi import Body, status, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from config import ENV_SETTINGS
from server.lib.report_generation.report_generator import create_time_sheets_report
from server.lib.database_manager import get_db_session
from server.web_api.web_security import token_is_valid, oauth_scheme

router = InferringRouter()


# pylint: disable=R0201
@cbv(router)
class ReportsRouter:
    """
    The API router responsible for defining endpoints relating to students.
    The defined endpoints allow HTTP requests to conduct create, read, update, and delete tasks on student records.
    """

    class Create:
        @staticmethod
        @router.get(ENV_SETTINGS.API_ROUTES.Reports.employee_reports, status_code=status.HTTP_201_CREATED)
        async def create_time_sheets_report(token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
            """
            An endpoint that creates a report from employee time sheet information.

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
            created_report_path = await create_time_sheets_report(session)
            return FileResponse(created_report_path)

