from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from fastapi import status, Depends, HTTPException
from config import ENV_SETTINGS
from server.lib.database_access.employee_hours_interface import get_employee_hours
from server.lib.database_manager import get_db_session
from server.web_api.models import ResponseModel
from server.web_api.web_security import oauth_scheme, token_is_valid

router = InferringRouter()


# pylint: disable=R0201
@cbv(router)
class EmployeesRouter:
    class Create:
        pass

    class Read:
        @router.get(ENV_SETTINGS.API_ROUTES.Timesheet.timesheet, status_code=status.HTTP_200_OK)
        def read_employee_work_hours(self, employee_id: str, date_start: str, date_end: str, token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
            """
            An endpoint to accumulate and return the total work hours, pto hours, overtime/extra hours for an employee within a provided date range.
            Front-end interaction can send requests to this endpoint with any valid date range, which would
            be useful for presenting total work hours over the course of a week, 2 weeks, a month, or a year.

            :param employee_id: The ID of the employee that the work hours should be calculated for.
            :type employee_id: str
            :param date_start: The starting date of the work hours to be calculated, provided in YYYY-MM-DD format.
            :type date_start: str
            :param date_end: The ending date of the work hours to be calculated, provided in YYYY-MM-DD format.
            :type date_end: str
            :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
            :type token: str, required
            :param session: The database session to use to retrieve all the employee data.
            :type session: sqlalchemy.orm.session, optional
            :return: A response model containing the total number of work hours from the days within the provided date range.
            :rtype: server.web_api.models.ResponseModel
            :raises HTTPException: If the provided employee has no hours logged into the system, or the employee does not exist in the database.
            """
            if not token_is_valid(token):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            total_hours = get_employee_hours(employee_id, date_start, date_end, session)
            if total_hours is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="The provided employee has no hours logged into the system, "
                                           "or the employee is not in the database!")
            return ResponseModel(status.HTTP_200_OK, "success", {"work_hours": total_hours[0], "pto_hours": total_hours[1], "extra_hours": total_hours[2]})

    class Update:
        pass

    class Delete:
        pass


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


