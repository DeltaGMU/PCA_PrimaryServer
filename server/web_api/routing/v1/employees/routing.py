"""
This module consists of FastAPI routing for Employees.
This handles all the REST API logic for creating, destroying, and updating employee-related data.
"""

from fastapi import Body, status, HTTPException
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from typing import Dict
from server.lib.utils.employee_utils import generate_employee_id, verify_employee_password, \
    create_employee_password_hashes
from server.web_api.models import ResponseModel
from server.lib.data_classes.employee import Employee, PydanticEmployee, EmployeeHours, PydanticEmployeeHours
from server.lib.service_manager import SharedData

router = InferringRouter()


# pylint: disable=R0201
@cbv(router)
class EmployeesRouter:
    """
    The API router responsible for defining endpoints relating to employees and employee hours.
    The defined endpoints allow HTTP requests to conduct timesheet-related operations with the employee entity.
    """

    @router.get("/api/v1/employees", status_code=status.HTTP_200_OK)
    def get_all_employees(self):
        """
        An endpoint that retrieves all the employees from the database and formats it into a list.

        :return: List of all employees found in the database. If there are no employees in the database, an empty list is returned.
        :rtype: server.web_api.models.ResponseModel
        """
        all_employees = []
        with SharedData().Managers.get_database_manager().make_session() as session:
            employees = session.query(Employee).all()
            # SELECT * FROM employee_table
            for row in employees:
                item: Employee = row
                all_employees.append(item.as_dict())
        return ResponseModel(status.HTTP_200_OK, "success", {"employees": all_employees})

    @router.post("/api/v1/employees/new", status_code=status.HTTP_201_CREATED)
    def create_new_employee(self, employee: PydanticEmployee):
        """
        An endpoint to create a new employee entity and adds it to the employees' table in the database.

        :param employee: The Pydantic Employee reference. This means that HTTP requests to this endpoint must include the required fields in the Pydantic Employee class.
        :type employee: PydanticEmployee
        :return: A response model containing the employee object that was created from the provided information with a generated employee ID and hashed password.
        :rtype: server.web_api.models.ResponseModel
        :raises HTTPException: If the provided request body contains an invalid plain text password, first name, or last name for the employee. This error may also be caused if the employee already exists in the database.
        """
        with SharedData().Managers.get_database_manager().make_session() as session:
            password_hash = create_employee_password_hashes(employee.RawPassword)
            if password_hash is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The plain text password provided to be hashed is invalid!")
            employee_id = generate_employee_id(employee.FirstName.strip(), employee.LastName.strip())
            if employee_id is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The employee first name or last name is invalid and cannot be used to create an employee ID!")
            try:
                new_employee = Employee(employee_id, employee.first_name, employee.last_name, password_hash)
                session.add(new_employee)
                session.commit()
            except IntegrityError as err:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
            created_employee = session.query(Employee).filter(Employee.employee_id == employee_id).one()
        return ResponseModel(status.HTTP_201_CREATED, "success", {"employee": created_employee})

    @router.post("/api/v1/employees/remove", status_code=status.HTTP_200_OK)
    def remove_employee(self, employee_id: Dict[str, str]):
        """
        An endpoint to remove an employee entity from the employee's table in the database.
        Removal of an employee using this endpoint will permanently delete the employee record from the database
        and all records related to the employee record in other tables through a cascading delete.

        :param employee_id: The ID of the employee that needs to be deleted, provided as a single entry. (Example: {"employee_id": jsmith123})
        :type employee_id: Dict[str, str]
        :return: A response model containing the employee object that was deleted from the database.
        :rtype: server.web_api.models.ResponseModel
        :raises HTTPException: If the provided request body contains an invalid employee ID, or if the employee does not exist in the database.
        """
        employee_id = employee_id.get('employee_id')
        if employee_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provided request body did not contain a valid employee id!")
        with SharedData().Managers.get_database_manager().make_session() as session:
            employee = session.query(Employee).filter(Employee.employee_id == employee_id).first()
            if employee:
                session.delete(employee)
                session.commit()
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove an employee that does not exist in the database!")
        return ResponseModel(status.HTTP_200_OK, "success", {"employee": employee})

    @router.get("/api/v1/employees/hours", status_code=status.HTTP_200_OK)
    def get_employee_hours(self, employee_id: str, date_start: str, date_end: str):
        """
        An endpoint to accumulate and return the total work hours for an employee within a provided date range.
        The total work hours calculated by this process only consists of the work hours for the days within the date range,
        and does not include leave hours, PTO, and extra/overtime hours.
        Front-end interaction can send requests to this endpoint with any valid date range, which would
        be useful for presenting total work hours over the course of a week, 2 weeks, a month, or a year.

        :param employee_id: The ID of the employee that the work hours should be calculated for.
        :type employee_id: str
        :param date_start: The starting date of the work hours to be calculated, provided in YYYY-MM-DD format.
        :type date_start: str
        :param date_end: The ending date of the work hours to be calculated, provided in YYYY-MM-DD format.
        :type date_end: str
        :return: A response model containing the total number of work hours from the days within the provided date range.
        :rtype: server.web_api.models.ResponseModel
        :raises HTTPException: If the provided employee has no hours logged into the system, or the employee does not exist in the database.
        """
        with SharedData().Managers.get_database_manager().make_session() as session:
            try:
                total_hours = session.query(func.sum(EmployeeHours.hours_worked).label('hours')).filter(
                    EmployeeHours.employee_id == employee_id,
                    EmployeeHours.date_worked.between(date_start, date_end)
                ).scalar()
                if total_hours is None:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                        detail="The provided employee has no hours logged into the system, "
                                               "or the employee is not in the database!")
            except IntegrityError as err:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
        return ResponseModel(status.HTTP_200_OK, "success", {"hours": total_hours})

    @router.post("/api/v1/employees/hours/add", status_code=status.HTTP_201_CREATED)
    def add_employee_hours(self, employee_hours: PydanticEmployeeHours):
        """
        An endpoint to add work hours for an employee on a specified date. Work hours cannot be added multiple times for the same day.

        :param employee_hours: The Pydantic EmployeeHours reference. This means that HTTP requests to this endpoint must include the required fields in the Pydantic EmployeeHours class.
        :type employee_hours: PydanticEmployeeHours
        :return: A response model containing the employee and employee hours data that has been added to the database.
        :rtype: server.web_api.models.ResponseModel
        :raises HTTPException: If the hours being added on the provided date is a duplicate entry, or the provided data is invalid.
        """
        with SharedData().Managers.get_database_manager().make_session() as session:
            try:
                work_hours_exists = session.query(EmployeeHours).filter(
                    EmployeeHours.employee_id == employee_hours.employee_id,
                    EmployeeHours.date_worked == employee_hours.date_worked
                ).all()
                if len(work_hours_exists) == 0:
                    total_employee_hours = EmployeeHours(
                        employee_hours.employee_id,
                        employee_hours.hours_worked,
                        employee_hours.date_worked
                    )
                    session.add(total_employee_hours)
                    session.commit()
                else:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Duplicate date entry! The employee already has hours entered for this day!")
            except IntegrityError as err:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
            created_employee_hours = session.query(EmployeeHours).filter(
                EmployeeHours.employee_id == employee_hours.employee_id,
                EmployeeHours.date_worked == employee_hours.date_worked
            ).one()
        return ResponseModel(status.HTTP_201_CREATED, "success", {"employee_hours": created_employee_hours})

    @router.get("/api/v1/employees/count", status_code=status.HTTP_200_OK)
    def get_employees_count(self):
        """
        An endpoint that counts the number of employees that are registered in the database.

        :return: A response model containing the number of employees in the database. The count will be 0 if there are no employees registered in the database.
        :rtype: server.web_api.models.ResponseModel
        """
        with SharedData().Managers.get_database_manager().make_session() as session:
            employees_count = session.query(Employee).count()
        return ResponseModel(status.HTTP_200_OK, "success", {"count": employees_count})

    @router.post("/api/v1/employees/verify", status_code=status.HTTP_200_OK)
    def verify_employee_password(self, employee_id: str = Body(""), password_text: str = Body("")):
        """
        An endpoint that is used to authenticate an employee by verifying the password provided in the request body is valid.
        This validation process is done by hashing and salting the plain text password provided in the request body from the web interface
        and compares it to the stored hashed password in the database. If both hashed passwords are equal, then the employee has successfully entered the correct credentials.

        :param employee_id: The ID of the employee that is attempting to authenticate their credentials with the server.
        :type employee_id: str
        :param password_text: The plain text password of the employee provided in the request body .
        :type password_text: str
        :return: A response model containing the validation of the password check. It will contain 'True' if the credentials were correct, or 'False' if they were incorrect.
        :rtype: server.web_api.models.ResponseModel
        """
        with SharedData().Managers.get_database_manager().make_session() as session:
            employee = session.query(Employee).filter(Employee.employee_id == employee_id).one()
            employee_verified = verify_employee_password(password_text, employee.PasswordHash)
            if employee_verified is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more provided parameters to verify the password hash is invalid!")
        return ResponseModel(status.HTTP_200_OK, "success", {"verified": employee_verified})
