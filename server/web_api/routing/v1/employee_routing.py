"""
This module consists of FastAPI routing for Employees.
This handles all the REST API logic for creating, reading, updating, and destroying employee-related data.
"""

from fastapi import status, HTTPException, Depends
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from server.web_api.api_routes import API_ROUTES
from server.web_api.models import ResponseModel
from server.lib.data_classes.employee import Employee, PydanticEmployeeRegistration, PydanticEmployeesRemoval, PydanticEmployeeUpdate, \
    PydanticRetrieveMultipleEmployees, PydanticMultipleEmployeesUpdate, PydanticUpdatePassword
from server.lib.database_manager import get_db_session
from server.lib.database_access.employee_interface import get_all_employees, get_employee, \
    create_employee, remove_employees, update_employee, get_multiple_employees, update_employees, is_admin, update_employee_password
from server.web_api.web_security import token_is_valid, oauth_scheme, get_user_from_token

router = InferringRouter()


# pylint: disable=R0201
@cbv(router)
class EmployeesRouter:
    class Create:
        @staticmethod
        @router.post(API_ROUTES.Employees.employees, status_code=status.HTTP_201_CREATED)
        async def register_new_employee(pyd_employee: PydanticEmployeeRegistration, token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
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
            if not await token_is_valid(token, ["administrator"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            created_employee = await create_employee(pyd_employee, session)
            return ResponseModel(status.HTTP_201_CREATED, "success", {"employee": created_employee})

    class Read:
        @staticmethod
        @router.get(API_ROUTES.Employees.count, status_code=status.HTTP_200_OK)
        async def read_employees_count(token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
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
            if not await token_is_valid(token, ["administrator"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            employees_count = session.query(Employee).count()
            return ResponseModel(status.HTTP_200_OK, "success", {"count": employees_count})

        @staticmethod
        @router.get(API_ROUTES.Employees.all_employees, status_code=status.HTTP_200_OK)
        async def read_all_employees(token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
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
            if not await token_is_valid(token, ["administrator"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            all_employees = await get_all_employees(session)
            all_employee_data = [employee.as_dict() for employee in all_employees]
            return ResponseModel(status.HTTP_200_OK, "success", {"count": len(all_employees), "employees": all_employee_data})

        @staticmethod
        @router.get(API_ROUTES.Employees.employee_token, status_code=status.HTTP_200_OK)
        async def read_employee_from_token(token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
            """
            An endpoint that retrieves the employee from the database that matches a provided valid access token.

            :param token: The JSON Web Token responsible for authenticating the user to this endpoint and to use to retrieve the employee.
            :type token: str, required
            :param session: The database session to use to retrieve the employee data.
            :type session: sqlalchemy.orm.session, optional
            :return: The employee found in the database that matches the provided access token. If there are no matching employees, an error is shown.
            :rtype: server.web_api.models.ResponseModel
            :raises HTTPException: If the authentication token is invalid or the employee does not exist.
            """
            if not await token_is_valid(token, ["employee"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            employee = await get_user_from_token(token, session)
            if employee is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The employee does not exist!")
            return ResponseModel(status.HTTP_200_OK, "success", {"employee": employee.as_dict()})

        @staticmethod
        @router.get(API_ROUTES.Employees.employees, status_code=status.HTTP_200_OK)
        async def read_multiple_employees(employee_ids: PydanticRetrieveMultipleEmployees, token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
            """
            An endpoint that retrieves a single employee from the database from the given employee ID

            :param employee_ids: The list of employee IDs.
            :type employee_ids: str, required
            :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
            :type token: str, required
            :param session: The database session to use to retrieve the employee data.
            :type session: sqlalchemy.orm.session, optional
            :return: The employees found in the database.
            :rtype: server.web_api.models.ResponseModel
            :raises HTTPException: If the authentication token is invalid, the provided request data is invalid, or one or more of the employees does not exist.
            """
            if not await token_is_valid(token, ["administrator"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            if len(employee_ids.employee_ids) == 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The employee ID list is empty! You must provide at least one employee ID to search for.")
            employees = await get_multiple_employees(employee_ids.employee_ids, session)
            if employees is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more employees in the provided list do not exist!")
            return ResponseModel(status.HTTP_200_OK, "success", {"employees": employees})

        @staticmethod
        @router.get(API_ROUTES.Employees.one_employee, status_code=status.HTTP_200_OK)
        async def read_one_employee(employee_id: str, token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
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
            if not await token_is_valid(token, ["employee"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            if employee_id is None or not isinstance(employee_id, str):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The employee ID must be a valid string!")
            employee = await get_user_from_token(token)
            if employee is None or (employee.EmployeeID != employee_id.strip() and not await is_admin(employee)):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="The user does not have permissions to view information about other employees.")
            employee = await get_employee(employee_id.strip(), session)
            if employee is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The employee could not be retrieved.")
            full_employee_information = employee.as_dict()
            return ResponseModel(status.HTTP_200_OK, "success", {"employee": full_employee_information})

    class Update:
        @staticmethod
        @router.put(API_ROUTES.Employees.employees, status_code=status.HTTP_200_OK)
        async def update_multiple_employees(multi_employee_update: PydanticMultipleEmployeesUpdate, token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
            """
            An endpoint that updates a single employee from the database from the provided employee information and employee ID.

            :param multi_employee_update: A dictionary that consists of pairs of employee IDs and update information as per the ``PydanticEmployeeUpdate`` parameters.
            :type multi_employee_update: PydanticMultipleEmployeesUpdate, required
            :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
            :type token: str, required
            :param session: The database session to use to update the employee data.
            :type session: sqlalchemy.orm.session, optional
            :return: A response model containing the employee updated in the database.
            :rtype: server.web_api.models.ResponseModel
            :raises HTTPException: If the authentication token is invalid or the employees could not be updated.
            """
            if not await token_is_valid(token, ["administrator"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            updated_employees = await update_employees(multi_employee_update.employee_updates, session)
            if updated_employees is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more provided parameters were invalid!")
            return ResponseModel(status.HTTP_200_OK, "success", {"employees": [employee.as_dict() for employee in updated_employees]})

        @staticmethod
        @router.put(API_ROUTES.Employees.one_employee, status_code=status.HTTP_200_OK)
        async def update_one_employee(employee_id: str, employee_update: PydanticEmployeeUpdate, token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
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
            :raises HTTPException: If the authentication token is invalid or the employee could not be updated.
            """
            if not await token_is_valid(token, ["employee"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            if employee_id is None or not isinstance(employee_id, str):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="The employee ID must be a valid string!")
            employee = await get_user_from_token(token)
            if employee is None or (employee.EmployeeID != employee_id.strip() and not await is_admin(employee)):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="The user does not have permissions to update information about other employees.")
            updated_employee = await update_employee(employee_id.strip(), employee_update, session)
            if updated_employee is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more provided parameters were invalid!")
            return ResponseModel(status.HTTP_200_OK, "success", {"employee": updated_employee.as_dict()})

        @staticmethod
        @router.put(API_ROUTES.Employees.password, status_code=status.HTTP_200_OK)
        async def update_employee_password(new_password: PydanticUpdatePassword, token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
            """
            An endpoint that updates a single employee's password from the database from the provided employee information and employee ID.

            :param new_password: The new password for the employee.
            :type new_password: str, required
            :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
            :type token: str, required
            :param session: The database session to use to update the employee data.
            :type session: sqlalchemy.orm.session, optional
            :return: A response model containing the employee updated in the database.
            :rtype: server.web_api.models.ResponseModel
            :raises HTTPException: If the authentication token is invalid or the employee could not be updated.
            """
            if not await token_is_valid(token, ["administrator"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            updated_employee = await update_employee_password(new_password.employee_id.strip(),
                                                              new_password.current_password.strip(),
                                                              new_password.new_password.strip(),
                                                              session)
            if updated_employee is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more provided parameters were invalid!")
            return ResponseModel(status.HTTP_200_OK, "success")

    class Delete:
        @staticmethod
        @router.post(API_ROUTES.Employees.remove_all_employees, status_code=status.HTTP_200_OK)
        async def delete_all_employees(are_you_sure: str, token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
            """
            An endpoint to remove ALL employee records from the employee's table in the database.
            Removal of multiple employees using this endpoint will permanently delete the employee records from the database
            and all records related to the employee records in other tables through a cascading delete.

            :param are_you_sure: An additional parameter that must say 'yes' to fulfill this request, to prevent accidental deletion.
            :type are_you_sure: str, required
            :param token: The JSON Web Token responsible for authenticating the user to this endpoint.
            :type token: str, required
            :param session: The database session to use to delete the employee records.
            :type session: sqlalchemy.orm.session, optional
            :return: A response model containing the number of employees deleted.
            :rtype: server.web_api.models.ResponseModel
            :raises HTTPException: If the provided request body contains invalid parameters.
            """
            if not await token_is_valid(token, ["administrator"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            if are_you_sure is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid parameters provided!")
            if are_you_sure.lower().strip() == 'yes':
                employees = session.query(Employee).all()
                for employee in employees:
                    session.delete(employee)
                session.commit()
            return ResponseModel(status.HTTP_200_OK, "success")

        @staticmethod
        @router.post(API_ROUTES.Employees.remove_employees, status_code=status.HTTP_200_OK)
        async def delete_employees(employee_ids: PydanticEmployeesRemoval, token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
            """
            An endpoint to remove multiple employee records from the employee's table in the database.
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
            if not await token_is_valid(token, ["administrator"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            removed_employees = await remove_employees(employee_ids, session)
            return ResponseModel(status.HTTP_200_OK, "success", {"employees": [employee.as_dict() for employee in removed_employees]})

        @staticmethod
        @router.post(API_ROUTES.Employees.remove_one_employee, status_code=status.HTTP_200_OK)
        async def delete_employee(employee_id: str, token: str = Depends(oauth_scheme), session=Depends(get_db_session)):
            """
            An endpoint to remove an employee record from the employee's table in the database.
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
            if not await token_is_valid(token, ["administrator"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired or is invalid!")
            if employee_id is None or not isinstance(employee_id, str):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="The employee ID must be a valid string!")
            removed_employees = await remove_employees(employee_id.strip(), session)
            return ResponseModel(status.HTTP_200_OK, "success", {"employee": [employee.as_dict() for employee in removed_employees]})

