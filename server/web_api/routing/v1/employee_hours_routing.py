from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from fastapi import status, Depends, HTTPException
from config import ENV_SETTINGS
from server.lib.database_access.employee_interface import is_admin
from server.lib.data_classes.employee_hours import PydanticReadEmployeeTimesheet, PydanticEmployeeMultipleTimesheetSubmission, PydanticEmployeeTimesheetUpdate, PydanticEmployeeTimesheetRemoval
from server.lib.database_access.employee_hours_interface import create_employee_multiple_hours, update_employee_hours, delete_employee_time_sheets, get_employee_hours_total
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
            An endpoint to submit multiple time sheets for an employee with the work hours, pto hours, overtime/extra hours on a provided date.
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
            if not await token_is_valid(token, ["teacher"]):
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
        @router.get(ENV_SETTINGS.API_ROUTES.Timesheet.one_timesheet, status_code=status.HTTP_200_OK)
        async def read_employee_time_sheets(employee_id: str, employee_hours: PydanticReadEmployeeTimesheet, token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
            """
            An endpoint to accumulate and return the total work hours, pto hours, overtime/extra hours for an employee within a provided date range.
            Front-end interaction can send requests to this endpoint with any valid date range, which would
            be useful for presenting total work hours over the course of a week, 2 weeks, a month, or a year.

            :param employee_id: The ID of the employee
            :type employee_id: str, required
            :param employee_hours: The starting date and the ending date of the total hours to be calculated.
            :type employee_hours: PydanticReadEmployeeTimesheet, required
            :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
            :type token: str, required
            :param session: The database session to use to retrieve all the employee data.
            :type session: sqlalchemy.orm.session, optional
            :return: A response model containing the total number of work hours, PTO hours, and extra/overtime hours from the days within the provided date range.
            :rtype: server.web_api.models.ResponseModel
            :raises HTTPException: If the provided employee has no hours logged into the system, or the employee does not exist in the database.
            """
            if not await token_is_valid(token, ["teacher"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            if employee_id is None or not isinstance(employee_id, str):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The employee ID must be a valid string!")
            employee = await get_user_from_token(token)
            if employee is None or (employee.EmployeeID != employee_id.strip() and not await is_admin(employee)):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="The user does not have sufficient permission.")
            if employee_hours.date_end is None:
                employee_hours.date_end = employee_hours.date_start
            total_hours_and_list = await get_employee_hours_total(employee_id.strip(), employee_hours.date_start, employee_hours.date_end, session)

            return ResponseModel(status.HTTP_200_OK, "success", total_hours_and_list)

    class Update:
        @staticmethod
        @router.put(ENV_SETTINGS.API_ROUTES.Timesheet.one_timesheet, status_code=status.HTTP_200_OK)
        async def update_employee_time_sheet(employee_id: str, updated_employee_hours: PydanticEmployeeTimesheetUpdate, token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
            if not await token_is_valid(token, ["teacher"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            if employee_id is None or not isinstance(employee_id, str):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The employee ID must be a valid string!")
            employee = await get_user_from_token(token, session)
            if employee is None or (employee.EmployeeID != employee_id.strip() and not await is_admin(employee, session)):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="The user does not have sufficient permissions.")
            updated_time_sheet = await update_employee_hours(employee_id, updated_employee_hours.date_worked,
                                                             updated_employee_hours.work_hours, updated_employee_hours.pto_hours,
                                                             updated_employee_hours.extra_hours, session)
            return ResponseModel(status.HTTP_200_OK, "success", {"time_sheet": updated_time_sheet.as_dict()})

    class Delete:
        @staticmethod
        @router.delete(ENV_SETTINGS.API_ROUTES.Timesheet.one_timesheet, status_code=status.HTTP_200_OK)
        async def delete_employee_time_sheet(employee_id: str, delete_employee_hours: PydanticEmployeeTimesheetRemoval,
                                             token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
            if not await token_is_valid(token, ["teacher"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            if employee_id is None or not isinstance(employee_id, str):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The employee ID must be a valid string!")
            employee = await get_user_from_token(token)
            if employee is None or (employee.EmployeeID != employee_id.strip() and not await is_admin(employee)):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="The user does not have sufficient permissions.")
            deleted_time_sheets = await delete_employee_time_sheets(employee_id, delete_employee_hours, session)
            return ResponseModel(status.HTTP_200_OK, "success", {"time_sheet": deleted_time_sheets})


'''
@router.post("/api/v1/employees/hours/add", status_code=status.HTTP_201_CREATED)
def add_employee_hours(pyd_employee_hours: PydanticEmployeeHours, session=Depends(get_db_session)):
    """
    An endpoint to add work hours for an employee on a specified date. Work hours cannot be added multiple times for the same day.

    :param pyd_employee_hours: The Pydantic EmployeeHours reference. This means that HTTP requests to this endpoint must include the required fields in the Pydantic EmployeeHours class.
    :type pyd_employee_hours: PydanticEmployeeHours
    :return: A response model containing the employee and employee hours data that has been added to the database.
    :rtype: server.web_api.models.ResponseModel
    :raises HTTPException: If the hours being added on the provided date is a duplicate entry, or the provided data is invalid.
    """

    try:
        work_hours_exists = session.query(EmployeeHours).filter(
            EmployeeHours.EmployeeID == pyd_employee_hours.employee_id,
            EmployeeHours.DateWorked == pyd_employee_hours.date_worked
        ).all()
        if len(work_hours_exists) == 0:
            total_employee_hours = EmployeeHours(
                pyd_employee_hours.employee_id,
                pyd_employee_hours.hours_worked,
                pyd_employee_hours.date_worked
            )
            session.add(total_employee_hours)
            session.commit()
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Duplicate date entry! The employee already has hours entered for this day!")
    except IntegrityError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    created_employee_hours = session.query(EmployeeHours).filter(
        EmployeeHours.EmployeeID == pyd_employee_hours.employee_id,
        EmployeeHours.DateWorked == pyd_employee_hours.date_worked
    ).one()
    return ResponseModel(status.HTTP_201_CREATED, "success", {"employee_hours": created_employee_hours.as_detail_dict()})
'''
