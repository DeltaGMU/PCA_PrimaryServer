"""
This module consists of FastAPI routing for Reports.
This handles all the REST API logic for creating reports for students and employees.
"""
from fastapi import Body, status, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from config import ENV_SETTINGS
from server.lib.database_access.student_grades_interface import delete_time_sheet_report_from_date, create_time_sheets_report, create_student_care_report
from server.lib.data_classes.report import PydanticDeleteReport, PydanticStudentRetrieveReport, PydanticEmployeeRetrieveReport
from server.lib.database_manager import get_db_session
from server.web_api.web_security import token_is_valid, oauth_scheme
from server.web_api.models import ResponseModel

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
        async def create_time_sheets_report(reporting_period: PydanticEmployeeRetrieveReport, token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
            """
            An endpoint that creates a report from employee time sheet information.

            :param reporting_period: The start and end dates of the time period to generate reports for.
            :type reporting_period: PydanticRetrieveEmployeeReport, required
            :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
            :type token: str, required
            :param session: The database session to use to create a new employee time sheet report.
            :type session: sqlalchemy.orm.session, optional
            :return: A response model containing the file path of the employee time sheet report that was created.
            :rtype: server.web_api.models.ResponseModel
            :raises HTTPException: If the request body contains any invalid parameters, or the data provided is formatted incorrectly.
            """
            if not await token_is_valid(token, ["administrator"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            created_report_path = await create_time_sheets_report(reporting_period.start_date, reporting_period.end_date, session)
            return FileResponse(created_report_path)

        @staticmethod
        @router.get(ENV_SETTINGS.API_ROUTES.Reports.care_reports, status_code=status.HTTP_201_CREATED)
        async def create_care_report(reporting_period: PydanticStudentRetrieveReport, token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
            """
            An endpoint that creates a report from student care service information.

            :param reporting_period: The start and end dates of the time period to generate reports for.
            :type reporting_period: PydanticRetrieveReport, required
            :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
            :type token: str, required
            :param session: The database session to use to create a new student care service report.
            :type session: sqlalchemy.orm.session, optional
            :return: A response model containing the file path of the student care service report that was created.
            :rtype: server.web_api.models.ResponseModel
            :raises HTTPException: If the request body contains any invalid parameters, or the data provided is formatted incorrectly.
            """
            if not await token_is_valid(token, ["administrator"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            created_report_path = await create_student_care_report(reporting_period.start_date, reporting_period.end_date, reporting_period.grade, session)
            return FileResponse(created_report_path)

    class Delete:
        @staticmethod
        @router.delete(ENV_SETTINGS.API_ROUTES.Reports.employee_reports, status_code=status.HTTP_200_OK)
        async def delete_time_sheets_report(reporting_period: PydanticDeleteReport, token: str = Depends(oauth_scheme)):
            """
            An endpoint that deletes an employee time sheet report provided the starting reporting period as a year and month in the YYYY-MM format.

            :param reporting_period: The date of the starting time period of the time sheet report in YYYY-MM format.
            :type reporting_period: PydanticDeleteReport, required
            :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
            :type token: str, required
            :return: A response model containing the file name of the deleted report.
            :rtype: server.web_api.models.ResponseModel
            :raises HTTPException: If the request body contains any invalid parameters, or the data provided is formatted incorrectly.
            """
            if not await token_is_valid(token, ["administrator"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            deleted_report_path = await delete_time_sheet_report_from_date(reporting_period.date)
            return ResponseModel(status.HTTP_200_OK, "success", {"report": deleted_report_path})
