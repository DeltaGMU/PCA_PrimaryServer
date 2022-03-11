from __future__ import annotations
from sqlalchemy.orm import Session
from typing import List, Dict
from server.lib.utils.employee_utils import generate_employee_id, create_employee_password_hashes
from server.lib.data_classes.employee import Employee, PydanticEmployeeRegistration, PydanticEmployeesRemoval, PydanticEmployeeUpdate, PydanticMultipleEmployeesUpdate
from server.lib.data_classes.employee_role import EmployeeRole
from server.lib.data_classes.contact_info import ContactInfo
from server.lib.database_manager import get_db_session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status


async def create_employee(pyd_employee: PydanticEmployeeRegistration, session: Session = None) -> Dict[str, any]:
    pyd_employee.first_name = pyd_employee.first_name.lower().strip()
    pyd_employee.last_name = pyd_employee.last_name.lower().strip()
    pyd_employee.primary_email = pyd_employee.primary_email.lower().strip()
    pyd_employee.role = pyd_employee.role.lower().strip()
    if pyd_employee.enable_notifications is None:
        pyd_employee.enable_notifications = True
    if pyd_employee.is_enabled is None:
        pyd_employee.is_enabled = True

    password_hash = await create_employee_password_hashes(pyd_employee.plain_password)
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
    contact_info = ContactInfo(employee_id, f"{pyd_employee.first_name} {pyd_employee.last_name}", pyd_employee.primary_email, pyd_employee.secondary_email, pyd_employee.enable_notifications)
    if contact_info is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The contact information for the employee could not be created due to invalid parameters!")
    session.add(contact_info)
    session.flush()

    # Create the employee and add it to the database.
    try:
        new_employee = Employee(employee_id, pyd_employee.first_name, pyd_employee.last_name, password_hash, role_query.id, contact_info.id, pyd_employee.is_enabled)
        session.add(new_employee)
        session.commit()
    except IntegrityError as err:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    # Retrieve the created employee from the database to ensure it has been properly added.
    created_employee = session.query(Employee).filter(Employee.EmployeeID == employee_id).one()
    created_employee = created_employee.as_detail_dict()
    # Add contact information elements into response for the web interface.
    created_employee['role_name'] = role_query.Name
    created_employee['primary_email'] = contact_info.PrimaryEmail
    created_employee['secondary_email'] = contact_info.SecondaryEmail
    created_employee['email_notifications_enabled'] = contact_info.EnableNotifications
    # Remove unnecessary elements from response for the web interface.
    del created_employee['password_hash']
    del created_employee['entry_created']
    del created_employee['role_id']
    del created_employee['contact_id']
    return created_employee


async def remove_employees(employee_ids: PydanticEmployeesRemoval | str, session: Session = None) -> List[Employee]:
    if isinstance(employee_ids, PydanticEmployeesRemoval):
        employee_ids = employee_ids.employee_ids
        if employee_ids is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provided request body did not contain any valid employee IDs!")
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
    if len(employee_updates) != all_updated_employees:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more employees were not able to be updated!")
    return all_updated_employees


async def update_employee(employee_id, pyd_employee_update: PydanticEmployeeUpdate, session: Session = None) -> Employee:
    if pyd_employee_update is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provided request body did not contain any valid employee information!")
    if employee_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The employee ID must be provided to update an employee!")

    # Get employee information from the database.
    employee = session.query(Employee).filter(Employee.EmployeeID == employee_id).first()
    if employee is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The employee id is incorrect or the employee does not exist!")
    employee_role = session.query(EmployeeRole).filter(EmployeeRole.id == employee.EmployeeRoleID).first()
    if employee_role is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The employee does not have role information registered, please do that first!")
    employee_contact_info = session.query(ContactInfo).filter(ContactInfo.id == employee.ContactInfoID).first()
    if employee_contact_info is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The employee does not have contact information registered, please do that first!")

    # Check to see what data was provided and update as necessary.
    if pyd_employee_update.plain_password:
        employee.PasswordHash = create_employee_password_hashes(pyd_employee_update.plain_password)
    if pyd_employee_update.first_name:
        employee.FirstName = pyd_employee_update.first_name
        employee_contact_info.FullNameOfContact = f"{employee.FirstName} {employee.LastName}"
    if pyd_employee_update.last_name:
        employee.LastName = pyd_employee_update.last_name
        employee_contact_info.FullNameOfContact = f"{employee.FirstName} {employee.LastName}"
    if pyd_employee_update.primary_email:
        employee_contact_info.PrimaryEmail = pyd_employee_update.primary_email
        employee_contact_info.LastUpdated = None
    if pyd_employee_update.secondary_email:
        employee_contact_info.SecondaryEmail = pyd_employee_update.secondary_email
        employee_contact_info.LastUpdated = None
    if pyd_employee_update.enable_notifications:
        employee_contact_info.EnableNotifications = pyd_employee_update.enable_notifications
        employee_contact_info.LastUpdated = None
    if pyd_employee_update.role:
        role_query = session.query(EmployeeRole).filter(EmployeeRole.Name == pyd_employee_update.role).first()
        if not role_query:
            session.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The provided employee role is invalid or does not exist!")
        employee.EmployeeRoleID = role_query.id
    if pyd_employee_update.is_enabled:
        employee.EmployeeEnabled = pyd_employee_update.is_enabled
    session.commit()
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
        matching_employee = session.query(Employee, ContactInfo).filter(
            Employee.ContactInfoID == ContactInfo.id,
            Employee.EmployeeID == ContactInfo.OwnerID,
            ContactInfo.PrimaryEmail == username
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


async def get_employee_contact_info(user: Employee, session: Session = None) -> ContactInfo:
    if user is None:
        raise RuntimeError('The user object was not provided! Please check for errors in the provided data!')
    if session is None:
        session = next(get_db_session())
    matching_contact = session.query(ContactInfo).filter(
        user.ContactInfoID == ContactInfo.id
    ).first()
    if matching_contact is None:
        raise RuntimeError('The employee contact information was not found using the user entity. Please check for errors in the database or the provided data!')
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


async def is_teacher(user: Employee, session: Session = None) -> bool:
    if user is None:
        raise RuntimeError('The user object was not provided! Please check for errors in the provided data!')
    employee_is_teacher: bool = await is_employee_role(user, 'teacher', session)
    if employee_is_teacher is None:
        raise RuntimeError('The employee role could not be retrieved for the provided user. Please check for errors in the database or the provided data!')
    return employee_is_teacher


async def get_employee_security_scopes(user: Employee, session: Session = None):
    if user is None:
        raise RuntimeError('The user object was not provided! Please check for errors in the provided data!')
    employee_role = await get_employee_role(user, session)
    if employee_role is None:
        raise RuntimeError('The employee role could not be retrieved for the provided user. Please check for errors in the database or the provided data!')
    if employee_role.Name == 'administrator':
        user_scopes = ['administrator', 'teacher']
    elif employee_role.Name == 'teacher':
        user_scopes = ['teacher']
    else:
        raise RuntimeError('The provided security scope is invalid! Please ensure that the security scope is in the database.')
    return user_scopes
