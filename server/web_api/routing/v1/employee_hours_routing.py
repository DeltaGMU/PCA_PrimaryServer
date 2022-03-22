from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from fastapi import status, Depends, HTTPException
from config import ENV_SETTINGS
from server.lib.database_access.employee_interface import is_admin
from server.lib.data_classes.employee_hours import PydanticEmployeeMultipleTimesheetSubmission, PydanticEmployeeTimesheetUpdate, PydanticEmployeeTimesheetRemoval
from server.lib.database_access.employee_hours_interface import create_employee_multiple_hours, update_employee_hours, delete_employee_time_sheets, get_employee_hours_total, delete_all_employee_time_sheets
from server.lib.database_manager import get_db_session
from server.web_api.models import ResponseModel
from server.web_api.web_security import oauth_scheme, token_is_valid, get_user_from_token

router = InferringRouter()


# pylint: disable=R0201
@cbv(router)
class EmployeeHoursRouter:
    class Create:
        @staticmethod
        @router.post(ENV_SETTINGS.API_ROUTES.Timesheet.one_timesheet, status_code=status.HTTP_201_CREATED)
        async def register_employee_time_sheets(employee_id: str, employee_time_sheets: PydanticEmployeeMultipleTimesheetSubmission, token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
            """
            An endpoint to submit (and/or update) multiple time sheets for an employee with the work hours, pto hours, overtime/extra hours on a provided date.
            Front-end interaction is required to provide an employee ID, work hours, and a work date. Providing PTO hours and extra/overtime hours
            are optional and will default to 0 for the date if not provided.

            :param employee_id: The ID of the employee
            :type employee_id: str, required
            :param employee_time_sheets: A list of elements with each of them containing the following: the work date, the work hours for the provided date, and additional hours such as PTO or extra/overtime hours.
            :type employee_time_sheets: PydanticEmployeeMultipleTimesheetSubmission, required
            :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
            :type token: str, required
            :param session: The database session to use to retrieve all the employee data.
            :type session: sqlalchemy.orm.session, optional
            :return: A response model containing the submitted timesheet consisting of the hours and the day worked.
            :rtype: server.web_api.models.ResponseModel
            :raises HTTPException: If the provided timesheet information is invalid, or the employee does not exist in the database.
            """
            if not await token_is_valid(token, ["employee"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            if employee_id is None or not isinstance(employee_id, str):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="The employee ID must be a valid string!")
            employee = await get_user_from_token(token)
            if employee is None or (employee.EmployeeID != employee_id.strip() and not await is_admin(employee)):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="The user does not have permissions to register time sheets for anyone except themselves.")
            created_time_sheets = await create_employee_multiple_hours(employee_id.strip(), employee_time_sheets.time_sheets, session)
            if created_time_sheets is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="The provided timesheet information is invalid or the employee is not registered in the database!")
            return ResponseModel(status.HTTP_201_CREATED, "success", {"time_sheets": [timesheet.as_dict() for timesheet in created_time_sheets]})

    class Read:
        @staticmethod
        @router.get(ENV_SETTINGS.API_ROUTES.Timesheet.hours_only, status_code=status.HTTP_200_OK)
        async def read_employee_time_sheet_hours(employee_id: str, date_start: str, date_end: str = None, token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
            """
            An endpoint to accumulate and return the total work hours, pto hours, overtime/extra hours for an employee within a provided date range without the full list of time sheets.
            Front-end interaction can send requests to this endpoint with any valid date range, which would
            be useful for presenting total work hours over the course of a week, 2 weeks, a month, or a year.


            :param employee_id: The ID of the employee.
            :type employee_id: str, required
            :param date_start: The starting date for the range of time sheets to query.
            :type date_start: str, required
            :param date_end: The ending date for the range of time sheets to query. If an ending date is not provided, it will only query the time sheets from the starting date.
            :type date_end: str, optional
            :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
            :type token: str, required
            :param session: The database session to use to retrieve all the employee data.
            :type session: sqlalchemy.orm.session, optional
            :return: A response model containing the total number of work hours, PTO hours, and extra/overtime hours from the days within the provided date range.
            :rtype: server.web_api.models.ResponseModel
            :raises HTTPException: If the provided employee has no hours logged into the system, or the employee does not exist in the database.
            """
            if not await token_is_valid(token, ["employee"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            if employee_id is None or not isinstance(employee_id, str):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The employee ID must be a valid string!")
            employee = await get_user_from_token(token)
            if employee is None or (employee.EmployeeID != employee_id.strip() and not await is_admin(employee)):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="The user does not have sufficient permission.")
            if date_end is None:
                date_end = date_start
            total_hours_and_list = await get_employee_hours_total(employee_id.strip(), date_start, date_end, session, hours_only=True)
            return ResponseModel(status.HTTP_200_OK, "success", total_hours_and_list)

        @staticmethod
        @router.get(ENV_SETTINGS.API_ROUTES.Timesheet.one_timesheet, status_code=status.HTTP_200_OK)
        async def read_employee_time_sheets(employee_id: str, date_start: str, date_end: str = None, token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
            """
            An endpoint to accumulate and return the total work hours, pto hours, overtime/extra hours for an employee within a provided date range.
            Front-end interaction can send requests to this endpoint with any valid date range, which would
            be useful for presenting total work hours over the course of a week, 2 weeks, a month, or a year.


            :param employee_id: The ID of the employee.
            :type employee_id: str, required
            :param date_start: The starting date for the range of time sheets to query.
            :type date_start: str, required
            :param date_end: The ending date for the range of time sheets to query. If an ending date is not provided, it will only query the time sheets from the starting date.
            :type date_end: str, optional
            :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
            :type token: str, required
            :param session: The database session to use to retrieve all the employee data.
            :type session: sqlalchemy.orm.session, optional
            :return: A response model containing the total number of work hours, PTO hours, and extra/overtime hours from the days within the provided date range.
            :rtype: server.web_api.models.ResponseModel
            :raises HTTPException: If the provided employee has no hours logged into the system, or the employee does not exist in the database.
            """
            if not await token_is_valid(token, ["employee"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            if employee_id is None or not isinstance(employee_id, str):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The employee ID must be a valid string!")
            employee = await get_user_from_token(token)
            if employee is None or (employee.EmployeeID != employee_id.strip() and not await is_admin(employee)):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="The user does not have sufficient permission.")
            if date_end is None:
                date_end = date_start
            total_hours_and_list = await get_employee_hours_total(employee_id.strip(), date_start, date_end, session)
            return ResponseModel(status.HTTP_200_OK, "success", total_hours_and_list)

    class Update:
        @staticmethod
        @router.put(ENV_SETTINGS.API_ROUTES.Timesheet.one_timesheet, status_code=status.HTTP_200_OK)
        async def update_employee_time_sheet(employee_id: str, updated_employee_hours: PydanticEmployeeTimesheetUpdate, token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
            """
            An endpoint to update the total work hours, pto hours, overtime/extra hours for an employee on a provided date.
            Front-end interaction can send requests to this endpoint with any valid date in YYYY-MM-DD format.

            :param employee_id: The ID of the employee.
            :type employee_id: str, required
            :param updated_employee_hours: The date, updated work/pto/extra hours, and comments.
            :type updated_employee_hours: PydanticEmployeeTimesheetUpdate, required
            :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
            :type token: str, required
            :param session: The database session to use to update the timesheet data.
            :type session: sqlalchemy.orm.session, optional
            :return: A response model containing the updated total number of work hours, PTO hours, and extra/overtime hours for the employee on the given date.
            :rtype: server.web_api.models.ResponseModel
            :raises HTTPException: If the provided employee has no hours logged into the system, or the employee does not exist in the database.
            """
            if not await token_is_valid(token, ["employee"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            if employee_id is None or not isinstance(employee_id, str):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The employee ID must be a valid string!")
            employee = await get_user_from_token(token, session)
            if employee is None or (employee.EmployeeID != employee_id.strip() and not await is_admin(employee, session)):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="The user does not have sufficient permissions.")
            updated_time_sheet = await update_employee_hours(employee_id, updated_employee_hours.date_worked,
                                                             updated_employee_hours.work_hours, updated_employee_hours.pto_hours,
                                                             updated_employee_hours.extra_hours, updated_employee_hours.comment, session)
            return ResponseModel(status.HTTP_200_OK, "success", {"time_sheet": updated_time_sheet.as_dict()})

    class Delete:
        @staticmethod
        @router.delete(ENV_SETTINGS.API_ROUTES.Timesheet.timesheet, status_code=status.HTTP_200_OK)
        async def remove_all_employee_time_sheets(employee_id: str, token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
            """
            An endpoint to delete all the time sheets for a specified employee.

            :param employee_id: The ID of the employee.
            :type employee_id: str, required
            :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
            :type token: str, required
            :param session: The database session to use to update the timesheet data.
            :type session: sqlalchemy.orm.session, optional
            :return: A response model displaying the success or failure of the deletion task.
            :rtype: server.web_api.models.ResponseModel
            :raises HTTPException: If the provided employee has no hours logged into the system, or the employee does not exist in the database.
            """
            if not await token_is_valid(token, ["administrator"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            if employee_id is None or not isinstance(employee_id, str):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The employee ID must be a valid string!")
            employee = await get_user_from_token(token)
            if employee is None or (employee.EmployeeID != employee_id.strip() and not await is_admin(employee)):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="The user does not have sufficient permissions.")
            await delete_all_employee_time_sheets(employee_id, session)
            return ResponseModel(status.HTTP_200_OK, "success")

        @staticmethod
        @router.delete(ENV_SETTINGS.API_ROUTES.Timesheet.one_timesheet, status_code=status.HTTP_200_OK)
        async def remove_employee_time_sheets(employee_id: str, delete_employee_hours: PydanticEmployeeTimesheetRemoval,
                                              token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
            """
            An endpoint to update the total work hours, pto hours, overtime/extra hours for an employee on a provided date.
            Front-end interaction can send requests to this endpoint with any valid date in YYYY-MM-DD format.

            :param employee_id: The ID of the employee.
            :type employee_id: str, required
            :param delete_employee_hours: The time sheets to delete on the provided date(s).
            :type delete_employee_hours: PydanticEmployeeTimesheetUpdate, required
            :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
            :type token: str, required
            :param session: The database session to use to update the timesheet data.
            :type session: sqlalchemy.orm.session, optional
            :return: A response model containing the deleted time sheets from the provided date(s).
            :rtype: server.web_api.models.ResponseModel
            :raises HTTPException: If the provided employee has no hours logged into the system, or the employee does not exist in the database.
            """
            if not await token_is_valid(token, ["employee"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            if employee_id is None or not isinstance(employee_id, str):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The employee ID must be a valid string!")
            employee = await get_user_from_token(token)
            if employee is None or (employee.EmployeeID != employee_id.strip() and not await is_admin(employee)):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="The user does not have sufficient permissions.")
            deleted_time_sheets = await delete_employee_time_sheets(employee_id, delete_employee_hours, session)
            return ResponseModel(status.HTTP_200_OK, "success", {"time_sheets": [time_sheet.as_dict() for time_sheet in deleted_time_sheets]})
