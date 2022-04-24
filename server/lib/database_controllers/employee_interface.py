from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy import sql
from typing import List, Dict
from random import randint

from server.lib.data_models.employee_hours import EmployeeHours
from server.lib.utils.email_utils import send_email
from server.lib.utils.employee_utils import generate_employee_id, create_employee_password_hashes, verify_employee_password
from server.lib.data_models.employee import Employee, PydanticEmployeeRegistration, PydanticEmployeesRemoval, PydanticEmployeeUpdate
from server.lib.data_models.employee_role import EmployeeRole
from server.lib.data_models.employee_contact_info import EmployeeContactInfo
from server.lib.database_manager import get_db_session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from fastapi import HTTPException, status


async def create_employee(pyd_employee: PydanticEmployeeRegistration, session: Session = None) -> Dict[str, any]:
    """
    This method creates a new employee account with all associated employee information such as
    employee contact information and employee role, and inserts the records into the database.
    When a new employee account is created, the employee password is automatically generated
    and sent to the employee's email. The employee may reset their password from the employee login portal.

    :param pyd_employee: The set of information required to register a new employee account, represented by the ``PydanticEmployeeRegistration`` pydantic class.
    :type pyd_employee: PydanticEmployeeRegistration, required
    :param session: The database session used to insert the employee information into the database.
    :type session: Session, optional
    :return: A JSON-Compatible dictionary containing the newly created employee account information.
    :rtype: Dict[str, any]
    :raises HTTPException: If any of the provided parameters are invalid, or a database error occurred during employee creation.
    """
    pyd_employee.first_name = pyd_employee.first_name.lower().strip()
    pyd_employee.last_name = pyd_employee.last_name.lower().strip()
    pyd_employee.primary_email = pyd_employee.primary_email.lower().strip()
    if pyd_employee.secondary_email:
        pyd_employee.secondary_email = pyd_employee.secondary_email.lower().strip()
        if pyd_employee.primary_email == pyd_employee.secondary_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The secondary email address cannot be the same as the primary email address!")
    pyd_employee.role = pyd_employee.role.lower().strip()
    if pyd_employee.enable_primary_email_notifications is None:
        pyd_employee.enable_primary_email_notifications = True
    if pyd_employee.enable_secondary_email_notifications is None or pyd_employee.secondary_email is None:
        pyd_employee.enable_secondary_email_notifications = False
    if pyd_employee.is_enabled is None:
        pyd_employee.is_enabled = True
    if pyd_employee.pto_hours_enabled is None:
        pyd_employee.pto_hours_enabled = True
    if pyd_employee.extra_hours_enabled is None:
        pyd_employee.extra_hours_enabled = True

    # Generate a temporary password.
    rand_characters = "".join([char.upper() if randint(0, 1) == 0 else char for char in pyd_employee.last_name])
    rand_numbers = "".join([str(randint(1, 9)) for _ in range(0, 4)])
    temp_password = f"{rand_characters}{rand_numbers}"
    password_hash = await create_employee_password_hashes(temp_password)
    if password_hash is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The plain text password provided to be hashed is invalid!")
    if len(pyd_employee.first_name) == 0 or len(pyd_employee.last_name) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The first and last name of the employee must not be empty!")
    if len(pyd_employee.role) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The employee role must not be empty!")
    if len(pyd_employee.primary_email) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The primary email must not be empty!")

    # Verify that the role is valid and return the role id for the specified role.
    role_query = session.query(EmployeeRole).filter(EmployeeRole.Name == pyd_employee.role).first()
    if not role_query:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The provided employee role is invalid or does not exist!")

    # Create employee ID.
    employee_id = await generate_employee_id(pyd_employee.first_name, pyd_employee.last_name, session)
    if employee_id is None:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The employee first name or last name is invalid and cannot be used to create an employee ID!")

    # Create employee contact information.
    contact_info = EmployeeContactInfo(employee_id, pyd_employee.primary_email, pyd_employee.secondary_email,
                                       pyd_employee.enable_primary_email_notifications, pyd_employee.enable_secondary_email_notifications)
    if contact_info is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The contact information for the employee could not be created due to invalid parameters!")

    # Create the employee and add it to the database.
    try:
        new_employee = Employee(employee_id, pyd_employee.first_name, pyd_employee.last_name, password_hash, role_query.id, contact_info,
                                pyd_employee.pto_hours_enabled, pyd_employee.extra_hours_enabled, pyd_employee.is_enabled)
        session.add(new_employee)
        session.commit()
    except IntegrityError as err:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    # Send notification to enabled emails that the account has been created.
    send_emails_to = [new_employee.EmployeeContactInfo.PrimaryEmail]
    if new_employee.EmployeeContactInfo.EnableSecondaryEmailNotifications:
        send_emails_to.append(new_employee.EmployeeContactInfo.SecondaryEmail)
    if len(send_emails_to) > 0:
        send_email(
            to_user=f'{new_employee.FirstName} {new_employee.LastName}',
            to_email=send_emails_to,
            subj="New Employee Account Registration Confirmed",
            messages=["Your employee account has been created!",
                      "Your login credentials are provided below, please be sure to change your temporary password as soon as possible.",
                      f"<b>Employee ID:</b> {new_employee.EmployeeID}",
                      f"<b>Temporary Password:</b> {temp_password}"],
        )
    return new_employee.as_dict()


async def remove_employees(employee_ids: PydanticEmployeesRemoval | str, session: Session = None) -> List[Employee]:
    """
    This method accepts one or more employee IDs and deletes the corresponding employee accounts from the database.
    Please note that employee accounts that have associated timesheet records cannot be deleted unless all
    timesheet records are removed.

    :param employee_ids: A single employee ID or a list of employee IDs to delete the corresponding employee account(s).
    :type employee_ids: PydanticEmployeesRemoval | str, required
    :param session: The database session used to delete one or more employee account records.
    :type session: Session, optional
    :return: The list of employee account records that have been deleted from the database.
    :rtype: List[Employee]
    :raises HTTPException: If any of the provided parameters are invalid, or the employee has associated timesheet records.
    """
    if session is None:
        session = next(get_db_session())
    if isinstance(employee_ids, PydanticEmployeesRemoval):
        employee_ids = employee_ids.employee_ids
        if employee_ids is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provided request body did not contain valid employee IDs!")
    removed_employees: List[Employee] = []
    if isinstance(employee_ids, List):
        employees = session.query(Employee).filter(Employee.EmployeeID.in_(employee_ids)).all()
        if employees:
            for employee in employees:
                if not check_employee_has_records(employee.EmployeeID):
                    session.delete(employee)
                    removed_employees.append(employee)
                else:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove employees that have timesheet records!")
            session.commit()
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove employees that do not exist in the database!")
    else:
        employee = session.query(Employee).filter(Employee.EmployeeID == employee_ids).first()
        if employee:
            session.delete(employee)
            removed_employees.append(employee)
            session.commit()
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove an employee that does not exist in the database!")
    return removed_employees


async def update_employees(employee_updates: Dict[str, PydanticEmployeeUpdate], session: Session = None) -> List[Employee]:
    """
    This method updates one or more employee account records with updated employee information provided in the form
    of a dictionary consisting of employee ID keys and employee update information values. Upon successful
    submission of an employee record, an email is sent to the employee notifying them that their account has been updated.

    :param employee_updates: A dictionary containing employee update information values paired with employee ID keys.
    :type employee_updates: Dict[str, PydanticEmployeeUpdate]
    :param session: The database session used to update one or more employee account records.
    :type session: Session, optional
    :return: A list of the employee account records that have been updated in the database.
    :rtype: List[Employee]
    :raises HTTPException: If any of the provided parameters are invalid.
    """
    if employee_updates is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provided request body did not contain any valid employee information!")
    all_updated_employees: List[Employee] = []
    for employee_id in employee_updates.keys():
        updated_employee = await update_employee(employee_id, employee_updates[employee_id], session)
        all_updated_employees.append(updated_employee)
    if len(employee_updates) != len(all_updated_employees):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more employees were not able to be updated!")
    return all_updated_employees


async def update_employee_password(employee_id: str, current_password: str, new_password: str, session: Session = None) -> Employee:
    """
    This method updates an existing employee account's password with a new password.
    The new employee password is provided as plain-text to this method which is then hashed and salted
    before being entered into the database.
    Upon a successful password change, the employee is sent an email notifying them that their account password
    has been updated.

    :param employee_id: The ID of the employee.
    :type employee_id: str, required
    :param current_password: The current plain-text password to the employee account.
    :type current_password: str, required
    :param new_password: The new plain-text password that the employee account should use.
    :type new_password: str, required
    :param session: The database session used to update the employee account's password.
    :type session: Session, optional
    :return: The employee account record that has had a password change.
    :rtype: Employee
    :raises HTTPException: If any of the provided parameters are invalid.
    """
    if employee_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The employee ID must be provided to update an employee!")
    if session is None:
        session = next(get_db_session())

    employee_id = employee_id.lower().strip()
    current_password = current_password.strip()
    new_password = new_password.strip()
    # Get employee information from the database.
    employee = session.query(Employee).filter(Employee.EmployeeID == employee_id).first()
    if employee is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The employee id is incorrect or the employee does not exist!")
    if not await verify_employee_password(current_password.strip(), employee.PasswordHash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The provided password does not match the account's password!")
    # Create the password hash + salt for the provided plain-text password.
    password_hash = await create_employee_password_hashes(new_password)
    if password_hash is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The plain text password provided to be hashed is invalid!")
    employee.PasswordHash = password_hash
    employee.LastUpdated = sql.func.now()
    session.commit()
    # Send notification to enabled emails that the account has had its password updated.
    send_emails_to = []
    if employee.EmployeeContactInfo.EnablePrimaryEmailNotifications:
        send_emails_to.append(employee.EmployeeContactInfo.PrimaryEmail)
    if employee.EmployeeContactInfo.EnableSecondaryEmailNotifications:
        send_emails_to.append(employee.EmployeeContactInfo.SecondaryEmail)
    if len(send_emails_to) > 0:
        send_email(
            to_user=f'{employee.FirstName} {employee.LastName}',
            to_email=send_emails_to,
            subj="Your Password Has Been Changed!",
            messages=[
                "Your employee account has had its password changed!",
                "If you don't remember changing your password or you're not aware of an administrator that has reset your password, please contact an administrator as soon as possible!"
            ],
        )
    return employee


async def update_employee(employee_id, pyd_employee_update: PydanticEmployeeUpdate, session: Session = None) -> Employee:
    """
    This method updates a single employee account record with updated employee information.
    Employee account passwords cannot be changed or updated using this method.
    Upon successful submission of the employee record, an email is sent to the employee notifying them that their account has been updated.

    :param employee_id: The ID of the employee.
    :type employee_id: str, required
    :param pyd_employee_update: The updated employee information that should be used.
    :type pyd_employee_update: PydanticEmployeeUpdate, required
    :param session: The database session used to update the employee record.
    :type session: Session, optional
    :return: The employee record that has been updated.
    :rtype: Employee
    """
    if pyd_employee_update is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provided request body did not contain any valid employee information!")
    if employee_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The employee ID must be provided to update an employee!")

    if session is None:
        session = next(get_db_session())

    # Get employee information from the database.
    employee = session.query(Employee).filter(Employee.EmployeeID == employee_id).first()
    if employee is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The employee id is incorrect or the employee does not exist!")
    employee_role = session.query(EmployeeRole).filter(EmployeeRole.id == employee.EmployeeRoleID).first()
    if employee_role is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The employee does not have role information registered, please do that first!")
    if employee.EmployeeContactInfo is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The employee does not have contact information registered, please do that first!")

    # Check to see what data was provided and update as necessary.
    if pyd_employee_update.first_name is not None:
        employee.FirstName = pyd_employee_update.first_name.lower().strip()
        employee.LastUpdated = sql.func.now()
    if pyd_employee_update.last_name is not None:
        employee.LastName = pyd_employee_update.last_name.lower().strip()
        employee.LastUpdated = sql.func.now()
    if pyd_employee_update.primary_email is not None:
        employee.EmployeeContactInfo.PrimaryEmail = pyd_employee_update.primary_email.lower().strip()
        employee.EmployeeContactInfo.LastUpdated = sql.func.now()
    if pyd_employee_update.secondary_email is not None:
        employee.EmployeeContactInfo.SecondaryEmail = pyd_employee_update.secondary_email.lower().strip()
        employee.EmployeeContactInfo.LastUpdated = sql.func.now()
    else:
        employee.EmployeeContactInfo.SecondaryEmail = None
        employee.EmployeeContactInfo.EnableSecondaryEmailNotifications = False
        employee.EmployeeContactInfo.LastUpdated = sql.func.now()
    if pyd_employee_update.enable_primary_email_notifications is not None:
        employee.EmployeeContactInfo.EnablePrimaryEmailNotifications = pyd_employee_update.enable_primary_email_notifications
        employee.EmployeeContactInfo.LastUpdated = sql.func.now()
    if pyd_employee_update.enable_secondary_email_notifications is not None:
        employee.EmployeeContactInfo.EnableSecondaryEmailNotifications = pyd_employee_update.enable_secondary_email_notifications
        employee.EmployeeContactInfo.LastUpdated = sql.func.now()
    if pyd_employee_update.role is not None:
        role_query = session.query(EmployeeRole).filter(EmployeeRole.Name == pyd_employee_update.role).first()
        if not role_query:
            session.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The provided employee role is invalid or does not exist!")
        employee.EmployeeRoleID = role_query.id
        employee.LastUpdated = sql.func.now()
    if pyd_employee_update.pto_hours_enabled is not None:
        employee.PTOHoursEnabled = pyd_employee_update.pto_hours_enabled
        employee.LastUpdated = sql.func.now()
    if pyd_employee_update.extra_hours_enabled is not None:
        employee.ExtraHoursEnabled = pyd_employee_update.extra_hours_enabled
        employee.LastUpdated = sql.func.now()
    if pyd_employee_update.is_enabled is not None:
        employee.EmployeeEnabled = pyd_employee_update.is_enabled
        employee.LastUpdated = sql.func.now()
    session.commit()
    # Send notification to enabled emails that the account has had its password updated.
    send_emails_to = []
    if employee.EmployeeContactInfo.EnablePrimaryEmailNotifications:
        send_emails_to.append(employee.EmployeeContactInfo.PrimaryEmail)
    if employee.EmployeeContactInfo.EnableSecondaryEmailNotifications:
        send_emails_to.append(employee.EmployeeContactInfo.SecondaryEmail)
    if len(send_emails_to) > 0:
        send_email(
            to_user=f'{employee.FirstName} {employee.LastName}',
            to_email=send_emails_to,
            subj="Your Employee Account Information Has Been Updated!",
            messages=[
                "Your employee account information has been updated!",
                "If you're not aware of updates to your account, please contact an administrator as soon as possible!"
            ],
        )
    return employee


async def check_employee_has_records(employee_id: str, session: Session = None) -> bool:
    """
    This utility method verifies if an employee account record has any associated saved time sheets.
    This method is useful in determining if an account is eligible to be deleted, since employee accounts
    with associated time sheets cannot be deleted.

    :param employee_id: The ID of the employee.
    :type employee_id: str, required
    :param session: The database session used to retrieve employee timesheet records for verification.
    :type session: Session, optional
    :return: True, if the employee has at least one timesheet record associated with the account.
    :rtype: bool
    """
    if session is None:
        session = next(get_db_session())
    if employee_id is None or not isinstance(employee_id, str):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The provided employee ID is invalid!")
    matching_employee = session.query(Employee).filter(
        Employee.EmployeeID == employee_id.strip()
    ).first()
    employee_has_time_sheets = session.query(EmployeeHours).filter(
        matching_employee.EmployeeID == EmployeeHours.EmployeeID,
        or_(EmployeeHours.WorkHours > 0, EmployeeHours.PTOHours > 0, EmployeeHours.ExtraHours > 0)
    ).all()
    if len(employee_has_time_sheets) > 0:
        return True
    return False


async def get_employee(username: str, session: Session = None) -> Employee:
    """
    This method is used to retrieve a single employee account record from the database provided
    either an employee ID or employee primary email. For accounts with the same primary email as another,
    only the account that was registered to that primary email first will be returned.
    It is highly advised to retrieve employees using an employee ID since they are guaranteed to be unique.

    :param username: The employee ID or the primary email of the employee account.
    :type username: str, required
    :param session: The database session used to retrieve the employee record.
    :type session: Session, optional
    :return: The employee account record associated with the employee ID or primary email.
    :rtype: Employee
    :raises HTTPException: If any of the provided parameters are invalid, or the employee ID or employee email does not correspond to any employee account record.
    """
    if session is None:
        session = next(get_db_session())
    username = username.strip().lower()
    if len(username) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='The username provided to the utility method to retrieve employee information is invalid due to a username length of 0!')

    # Check by employee ID first, if an email was provided instead, check by email.
    matching_employee = session.query(Employee).filter(
        Employee.EmployeeID == username
    ).first()
    if matching_employee is None:
        matching_employee = session.query(Employee, EmployeeContactInfo).filter(
            Employee.EmployeeID == EmployeeContactInfo.EmployeeID,
            EmployeeContactInfo.PrimaryEmail == username
        ).first()
        if matching_employee is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='The employee was not found by the employee ID or the employee email. Please check for errors in the provided data!')
        matching_employee = matching_employee[0]
    return matching_employee


async def get_multiple_employees(employee_ids: List[str], session: Session = None) -> List[Employee]:
    """
    This method is used to retrieve multiple employee account records for a list of employee IDs.

    :param employee_ids: A list of employee IDs.
    :type employee_ids: List[str]
    :param session: The database session used to retrieve the list of employee account records.
    :type session: Session, optional
    :return: A list of employee account records corresponding to the provided employee IDs.
    :rtype: List[Employee]
    :raises HTTPException: If any of the provided parameters are invalid, or if one or more provided employee IDs do not correspond to an employee account record.
    """
    if session is None:
        session = next(get_db_session())
    if None in employee_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='All the employee IDs provided must be valid strings. Please check for errors in the provided data!')
    matching_employees = session.query(Employee).filter(
        Employee.EmployeeID.in_(employee_ids)
    ).all()
    if matching_employees is None or len(matching_employees) != len(employee_ids):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='One or more employee IDs provided are invalid! Please check for spelling errors.')
    all_employees_data = [employee.as_dict() for employee in matching_employees]
    return all_employees_data


async def get_all_employees(session: Session = None) -> List[Employee]:
    """
    This method is used to retrieve all the employee account records stored in the database.
    This includes all employee accounts that may be disabled.

    :param session: The database session used to retrieve all the employee account records.
    :type session: Session, optional
    :return: A list of all the employee account records in the database.
    :rtype: List[Employee]
    """
    if session is None:
        session = next(get_db_session())
    all_employees = []
    employees = session.query(Employee).all()
    for employee in employees:
        all_employees.append(employee)
    return all_employees


async def get_employee_role(user: Employee, session: Session = None) -> EmployeeRole:
    """
    This method is used to retrieve an employee account record's employee role.
    If you need to retrieve the employee role without a reference to the employee account record,
    then consider retrieving that record first before using this method.

    :param user: The employee account record to retrieve the employee role from.
    :type user: Employee
    :param session: The database session used to retrieve the employee account's role.
    :type session: Session, optional
    :return: The employee role associated with the employee account record.
    :rtype: EmployeeRole
    :raises HTTPException: If the employee entity provided is null or if there is no employee role associated with the employee account record.
    """
    if user is None:
        raise RuntimeError('The user object was not provided! Please check for errors in the provided data!')
    if session is None:
        session = next(get_db_session())
    matching_role = session.query(EmployeeRole).filter(
        EmployeeRole.id == user.EmployeeRoleID
    ).first()
    if matching_role is None:
        raise RuntimeError('The employee role was not found using the user entity. Please check for errors in the database or the provided data!')
    return matching_role


async def get_employee_contact_info(employee_id: str, session: Session = None) -> EmployeeContactInfo:
    """
    This method is used to retrieve an employee account record's contact information.

    :param employee_id: The ID of the employee.
    :type employee_id: str, required
    :param session: The database session used to retrieve the employee contact information.
    :type session: Session, optional
    :return: The employee contact information associated with the provided employee ID.
    :rtype: EmployeeContactInfo
    :raises RuntimeError: If the employee ID is null or if there is no employee contact information associated with the employee account.
    """
    if employee_id is None:
        raise RuntimeError('The employee ID was not provided! Please check for errors in the provided data!')
    if session is None:
        session = next(get_db_session())
    matching_employee = session.query(Employee).filter(
        Employee.EmployeeID == employee_id
    ).first()
    matching_contact = matching_employee.EmployeeContactInfo
    if matching_contact is None:
        raise RuntimeError('The employee contact information was not found using the employee ID. Please check for errors in the database or the provided data!')
    return matching_contact


async def is_employee_role(user: Employee, role_name: str, session: Session = None) -> bool:
    """
    This utility method is used to check if an employee account has a specific employee role
    that matches the provided role name.

    :param user: The employee account record to check the role information for.
    :type user: Employee
    :param role_name: The name of the employee role that needs to be compared with the employee account record's role.
    :type role_name: str, required
    :param session: The database session used to retrieve and verify the employee account role.
    :type session: Session, optional
    :return: True if the employee account role matches the provided role name.
    :rtype: bool
    :raises RuntimeError: If the employee ID is null or if there is no employee role associated with the employee account.
    """
    if None in (user, role_name):
        raise RuntimeError('The user or employee role was not provided to the employee role check method. Please check for errors in the provided data!')
    employee_role: EmployeeRole = await get_employee_role(user, session)
    if employee_role is None:
        raise RuntimeError('The employee role could not be retrieved for the provided user. Please check for errors in the database or the provided data!')
    return employee_role.Name == role_name


async def is_admin(user: Employee, session: Session = None) -> bool:
    """
    This utility method is used to verify if the provided employee account record has administrative privileges.

    :param user: The employee account record to check the role information for.
    :type user: Employee
    :param session: The database session used to retrieve and verify the employee account role.
    :type session: Session, optional
    :return: True if the employee account provided is an administrator role.
    :rtype: bool
    :raises RuntimeError: If the provided employee record is null or if the employee role could not be retrieved from the database for verification.
    """
    if user is None:
        raise RuntimeError('The user object was not provided! Please check for errors in the provided data!')
    employee_is_admin: bool = await is_employee_role(user, 'administrator', session)
    if employee_is_admin is None:
        raise RuntimeError('The employee role could not be retrieved for the provided user. Please check for errors in the database or the provided data!')
    return employee_is_admin


async def is_employee(user: Employee, session: Session = None) -> bool:
    """
    This utility method is used to verify if the provided employee account record has regular employee privileges.

    :param user: The employee account record to check the role information for.
    :type user: Employee
    :param session: The database session used to retrieve and verify the employee account role.
    :type session: Session, optional
    :return: True if the employee account provided is an employee role.
    :rtype: bool
    :raises RuntimeError: If the provided employee record is null or if the employee role could not be retrieved from the database for verification.
    """
    if user is None:
        raise RuntimeError('The user object was not provided! Please check for errors in the provided data!')
    pca_employee: bool = await is_employee_role(user, 'employee', session)
    if pca_employee is None:
        raise RuntimeError('The employee role could not be retrieved for the provided user. Please check for errors in the database or the provided data!')
    return pca_employee


async def get_employee_security_scopes(user: Employee, session: Session = None) -> List[str]:
    """
    This utility method retrieves the security scopes associated with an employee account record.
    Higher privilege roles have greater security scopes and access rights within the API.

    :param user: The employee account record to check the security scopes for.
    :type user: Employee
    :param session: The database session used to retrieve and verify the employee account security scopes.
    :type session: Session, optional
    :return: A list of the security scopes associated with the provided employee account record.
    :rtype: List[str]
    :raises RuntimeError: If the provided employee record is null or if the employee's security scopes could not be retrieved.
    """
    if user is None:
        raise RuntimeError('The user object was not provided! Please check for errors in the provided data!')
    employee_role = await get_employee_role(user, session)
    if employee_role is None:
        raise RuntimeError('The employee role could not be retrieved for the provided user. Please check for errors in the database or the provided data!')
    if employee_role.Name == 'administrator':
        user_scopes = ['administrator', 'employee']
    elif employee_role.Name == 'employee':
        user_scopes = ['employee']
    else:
        raise RuntimeError('The provided security scope is invalid! Please ensure that the security scope (role) is in the database.')
    return user_scopes
