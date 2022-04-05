from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy import sql
from typing import List, Dict
from random import choice, randint
from server.lib.utils.email_utils import send_email
from server.lib.utils.employee_utils import generate_employee_id, create_employee_password_hashes, verify_employee_password
from server.lib.data_classes.employee import Employee, PydanticEmployeeRegistration, PydanticEmployeesRemoval, PydanticEmployeeUpdate
from server.lib.data_classes.employee_role import EmployeeRole
from server.lib.data_classes.employee_contact_info import EmployeeContactInfo
from server.lib.database_manager import get_db_session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status


async def create_employee(pyd_employee: PydanticEmployeeRegistration, session: Session = None) -> Dict[str, any]:
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
    # session.add(contact_info)
    # session.flush()

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
                session.delete(employee)
                removed_employees.append(employee)
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
    if employee_updates is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provided request body did not contain any valid employee information!")
    all_updated_employees: List[Employee] = []
    for employee_id in employee_updates.keys():
        updated_employee = await update_employee(employee_id, employee_updates[employee_id], session)
        all_updated_employees.append(updated_employee)
    if len(employee_updates) != len(all_updated_employees):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more employees were not able to be updated!")
    return all_updated_employees


async def update_employee_password(employee_id: str, current_password: str, new_password: str, session: Session = None):
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


async def get_employee(username: str, session: Session = None) -> Employee:
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
    if session is None:
        session = next(get_db_session())
    all_employees = []
    employees = session.query(Employee).all()
    for employee in employees:
        all_employees.append(employee)
    return all_employees


async def get_employee_role(user: Employee, session: Session = None) -> EmployeeRole:
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
    if None in (user, role_name):
        raise RuntimeError('The user or employee role was not provided to the employee role check method. Please check for errors in the provided data!')
    employee_role: EmployeeRole = await get_employee_role(user, session)
    if employee_role is None:
        raise RuntimeError('The employee role could not be retrieved for the provided user. Please check for errors in the database or the provided data!')
    return employee_role.Name == role_name


async def is_admin(user: Employee, session: Session = None) -> bool:
    if user is None:
        raise RuntimeError('The user object was not provided! Please check for errors in the provided data!')
    employee_is_admin: bool = await is_employee_role(user, 'administrator', session)
    if employee_is_admin is None:
        raise RuntimeError('The employee role could not be retrieved for the provided user. Please check for errors in the database or the provided data!')
    return employee_is_admin


async def is_employee(user: Employee, session: Session = None) -> bool:
    if user is None:
        raise RuntimeError('The user object was not provided! Please check for errors in the provided data!')
    pca_employee: bool = await is_employee_role(user, 'employee', session)
    if pca_employee is None:
        raise RuntimeError('The employee role could not be retrieved for the provided user. Please check for errors in the database or the provided data!')
    return pca_employee


async def get_employee_security_scopes(user: Employee, session: Session = None):
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
        raise RuntimeError('The provided security scope is invalid! Please ensure that the security scope is in the database.')
    return user_scopes
