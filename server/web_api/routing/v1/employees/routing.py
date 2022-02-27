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
    Router class for employees api.
    """

    @router.get("/api/v1/employees", status_code=status.HTTP_200_OK)
    def get_all_employees(self):
        """
        Retrieves all the employees from the database.
        :return: list of all employees in the database
        :rtype: ResponseModel
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
        Creates a new employee entity and adds it to the employees' table in the database.

        :param employee: The Pydantic employee reference.
        :type employee: PydanticEmployee
        :return: created employee
        :rtype: ResponseModel
        """
        with SharedData().Managers.get_database_manager().make_session() as session:
            password_hash = create_employee_password_hashes(employee.RawPassword)
            if password_hash is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The plain text password provided to be hashed is invalid!")
            employee_id = generate_employee_id(employee.FirstName.strip(), employee.LastName.strip())
            if employee_id is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The employee first name or last name is invalid and cannot be used to create an employee ID!")
            try:
                new_employee = Employee(employee_id, employee.FirstName, employee.LastName, password_hash, employee.EmployeeEnabled)
                session.add(new_employee)
                session.commit()
            except IntegrityError as err:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
            created_employee = session.query(Employee).filter(Employee.EmployeeID == employee_id).one()
        return ResponseModel(status.HTTP_201_CREATED, "success", {"employee": created_employee})

    @router.post("/api/v1/employees/remove", status_code=status.HTTP_200_OK)
    def remove_employee(self, employee_id: Dict[str, str]):
        employee_id = employee_id.get('employee_id')
        if employee_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provided request body did not contain a valid employee id!")
        with SharedData().Managers.get_database_manager().make_session() as session:
            employee = session.query(Employee).filter(Employee.EmployeeID == employee_id).first()
            if employee:
                session.delete(employee)
                session.commit()
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove an employee that does not exist in the database!")
        return ResponseModel(status.HTTP_200_OK, "success", {"employee": employee})

    @router.get("/api/v1/employees/hours", status_code=status.HTTP_200_OK)
    def get_employee_hours(self, employee_id: str, date_start: str, date_end: str):
        with SharedData().Managers.get_database_manager().make_session() as session:
            try:
                total_hours = session.query(func.sum(EmployeeHours.HoursWorked).label('hours')).filter(
                    EmployeeHours.EmployeeID == employee_id,
                    EmployeeHours.DateWorked.between(date_start, date_end)
                ).scalar()
                if total_hours is None:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                        detail="The provided employee has no hours logged into the system, "
                                               "or the employee is not in the database!")
            except IntegrityError as err:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from err
        return ResponseModel(status.HTTP_200_OK, "success", {"hours": total_hours})

    @router.post("/api/v1/employees/hours/add", status_code=status.HTTP_201_CREATED)
    def add_employee_hours(self, employee_hours: PydanticEmployeeHours):
        with SharedData().Managers.get_database_manager().make_session() as session:
            try:
                work_hours_exists = session.query(EmployeeHours).filter(
                    EmployeeHours.EmployeeID == employee_hours.EmployeeID,
                    EmployeeHours.DateWorked == employee_hours.DateWorked
                ).all()
                if len(work_hours_exists) == 0:
                    total_employee_hours = EmployeeHours(
                        employee_hours.EmployeeID,
                        employee_hours.HoursWorked,
                        employee_hours.DateWorked
                    )
                    session.add(total_employee_hours)
                    session.commit()
                else:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Duplicate date entry! The employee already has hours entered for this day!")
            except IntegrityError as err:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from err
            created_employee_hours = session.query(EmployeeHours).filter(
                EmployeeHours.EmployeeID == employee_hours.EmployeeID,
                EmployeeHours.DateWorked == employee_hours.DateWorked
            ).one()
        return ResponseModel(status.HTTP_201_CREATED, "success", {"employee_hours": created_employee_hours})

    @router.get("/api/v1/employees/count", status_code=status.HTTP_200_OK)
    def get_employees_count(self):
        with SharedData().Managers.get_database_manager().make_session() as session:
            employees_count = session.query(Employee).count()
        return ResponseModel(status.HTTP_200_OK, "success", {"count": employees_count})

    @router.post("/api/v1/employees/verify", status_code=status.HTTP_200_OK)
    def verify_employee_password(self, employee_id: str = Body(""), password_text: str = Body("")):
        with SharedData().Managers.get_database_manager().make_session() as session:
            employee = session.query(Employee).filter(Employee.EmployeeID == employee_id).one()
            employee_verified = verify_employee_password(password_text, employee.PasswordHash)
            if employee_verified is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more provided parameters to verify the password hash is invalid!")
        return ResponseModel(status.HTTP_200_OK, "success", {"verified": employee_verified})
