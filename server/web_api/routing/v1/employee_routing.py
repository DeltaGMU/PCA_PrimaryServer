"""
This module consists of FastAPI routing for Employees.
This handles all the REST API logic for creating, reading, updating, and destroying employee-related data.
"""

from fastapi import Body, status, HTTPException, Depends, Security
from fastapi.routing import APIRouter
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from config import ENV_SETTINGS
from server.web_api.models import ResponseModel
from server.lib.data_classes.employee import Employee, PydanticEmployeeRegistration, PydanticEmployeesRemoval, PydanticEmployeeUpdate
from server.lib.database_manager import get_db_session
from server.lib.database_functions.employee_interface import get_employee_role, get_employee_contact_info, get_all_employees, get_employee, \
    create_employee, remove_employees, update_employee
from server.web_api.web_security import token_is_valid, oauth_scheme, get_user_from_token

router = APIRouter()


# pylint: disable=R0201

@router.post(ENV_SETTINGS.API_ROUTES.register, status_code=status.HTTP_201_CREATED)
def register_new_employee(pyd_employee: PydanticEmployeeRegistration, token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
    """
    An endpoint to create a new employee entity and adds it to the employees' table in the database.

    :param pyd_employee: The Pydantic Employee Registration reference. This means that HTTP requests to this endpoint must include the required fields in the ``PydanticEmployeeRegistration``.
    :type pyd_employee: PydanticEmployeeRegistration, required
    :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
    :type token: str, required
    :param session: The database session to use to register a new employee.
    :type session: sqlalchemy.orm.Session, optional
    :return: A response model containing the employee object that was created from the provided information with a generated employee ID and hashed password.
    :rtype: server.web_api.models.ResponseModel
    :raises HTTPException: If the provided request body contains any invalid parameters for the employee. This error may also be caused if the employee already exists in the database.
    """
    if not token_is_valid(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
    created_employee = create_employee(pyd_employee, session)
    return ResponseModel(status.HTTP_201_CREATED, "success", {"employee": created_employee})


@router.get(ENV_SETTINGS.API_ROUTES.Employees.count, status_code=status.HTTP_200_OK)
def read_employees_count(token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
    """
    An endpoint that counts the number of employees that are registered in the database.

    :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
    :type token: str, required
    :param session: The database session to use to retrieve all the employee data.
    :type session: sqlalchemy.orm.session, optional
    :return: A response model containing the number of employees found in the database.
    :rtype: server.web_api.models.ResponseModel
    :raises HTTPException: If the authentication token is invalid.
    """
    if not token_is_valid(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
    employees_count = session.query(Employee).count()
    return ResponseModel(status.HTTP_200_OK, "success", {"count": employees_count})


@router.get(ENV_SETTINGS.API_ROUTES.Employees.employees, status_code=status.HTTP_200_OK)
def read_all_employees(token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
    """
    An endpoint that retrieves all the employees from the database and formats it into a list.

    :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
    :type token: str, required
    :param session: The database session to use to retrieve all the employee data.
    :type session: sqlalchemy.orm.session, optional
    :return: List of all employees found in the database with the total count of employees. If there are no employees in the database, an empty list and a count of 0 is returned.
    :rtype: server.web_api.models.ResponseModel
    :raises HTTPException: If the authentication token is invalid.
    """
    if not token_is_valid(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
    all_employees = get_all_employees(session)
    all_employee_data = [employee.as_dict() for employee in all_employees]
    return ResponseModel(status.HTTP_200_OK, "success", {"count": len(all_employees), "employees": all_employee_data})


@router.get(ENV_SETTINGS.API_ROUTES.Employees.employee_token, status_code=status.HTTP_200_OK)
def read_employee_from_token(token: str = Depends(oauth_scheme)):
    if not token_is_valid(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
    employee = get_user_from_token(token)
    if employee is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The employee does not exist!")
    return ResponseModel(status.HTTP_200_OK, "success", {"employee": employee.as_dict()})


@router.get(ENV_SETTINGS.API_ROUTES.Employees.employee, status_code=status.HTTP_200_OK)
def read_one_employee(employee_id: str, token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
    """
    An endpoint that retrieves a single employee from the database from the given employee ID

    :param employee_id: The ID of the employee.
    :type employee_id: str, required
    :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
    :type token: str, required
    :param session: The database session to use to retrieve the employee data.
    :type session: sqlalchemy.orm.session, optional
    :return: The employees found in the database.
    :rtype: server.web_api.models.ResponseModel
    :raises HTTPException: If the authentication token is invalid or the employee could not be retrieved.
    """
    if not token_is_valid(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
    employee = get_employee(employee_id)
    if employee is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The employee could not be retrieved.")
    full_employee_information = get_employee(employee, session)
    full_employee_information.update(get_employee_contact_info(employee))
    full_employee_information.update(get_employee_role(employee))
    return ResponseModel(status.HTTP_200_OK, "success", {"employee": full_employee_information})


@router.put(ENV_SETTINGS.API_ROUTES.Employees.employee, status_code=status.HTTP_200_OK)
def update_one_employee(employee_id: str, employee_update: PydanticEmployeeUpdate, token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
    """
    An endpoint that updates a single employee from the database from the provided employee information and employee ID.

    :param employee_id: The ID of the employee.
    :type employee_id: str, required
    :param employee_update: The ID of the employee and any other employee information that needs to be updated.
    :type employee_update: PydanticEmployeeUpdate, required
    :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
    :type token: str, required
    :param session: The database session to use to update the employee data.
    :type session: sqlalchemy.orm.session, optional
    :return: A response model containing the employee updated in the database.
    :rtype: server.web_api.models.ResponseModel
    :raises HTTPException: If the authentication token is invalid or the employee could not be retrieved.
    """
    if not token_is_valid(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
    updated_employee = update_employee(employee_id, employee_update, session)
    if updated_employee is None:
        raise HTTPException(status_cpde=status.HTTP_400_BAD_REQUEST, detail="One or more provided parameters were invalid!")
    return ResponseModel(status.HTTP_200_OK, "success", {"employee": updated_employee.as_dict()})


@router.delete(ENV_SETTINGS.API_ROUTES.Employees.employees, status_code=status.HTTP_200_OK)
def delete_employees(employee_ids: PydanticEmployeesRemoval, token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
    """
    An endpoint to remove multiple employee entity from the employee's table in the database.
    Removal of multiple employees using this endpoint will permanently delete the employee records from the database
    and all records related to the employee records in other tables through a cascading delete.
    To remove multiple employee records, the employee IDs must be provided in a list.

    :param employee_ids: A list of IDs of employees that needs to be deleted.
    :type employee_ids: PydanticEmployeeRemoval, required
    :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
    :type token: str, required
    :param session: The database session to use to delete the employee record.
    :type session: sqlalchemy.orm.session, optional
    :return: A response model containing the employee object that was deleted from the database.
    :rtype: server.web_api.models.ResponseModel
    :raises HTTPException: If the provided request body contains an invalid employee ID, or if the employee does not exist in the database.
    """
    if not token_is_valid(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
    removed_employees = remove_employees(employee_ids, session)
    return ResponseModel(status.HTTP_200_OK, "success", {"employees": [employee.as_dict() for employee in removed_employees]})


@router.delete(ENV_SETTINGS.API_ROUTES.Employees.employee, status_code=status.HTTP_200_OK)
def delete_employee(employee_id: str, token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
    """
    An endpoint to remove an employee entity from the employee's table in the database.
    Removal of an employee using this endpoint will permanently delete the employee record from the database
    and all records related to the employee record in other tables through a cascading delete.

    :param employee_id: The ID of the employee that needs to be deleted.
    :type employee_id: str, required
    :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
    :type token: str, required
    :param session: The database session to use to delete the employee record.
    :type session: sqlalchemy.orm.session, optional
    :return: A response model containing the employee object that was deleted from the database.
    :rtype: server.web_api.models.ResponseModel
    :raises HTTPException: If the provided request body contains an invalid employee ID, or if the employee does not exist in the database.
    """
    if not token_is_valid(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
    removed_employees = remove_employees(employee_id, session)
    return ResponseModel(status.HTTP_200_OK, "success", {"employee": [employee.as_dict() for employee in removed_employees]})
