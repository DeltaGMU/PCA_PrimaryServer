"""
The employee utility module contains multiple utility methods that serve to help employee-related tasks.
For example, the ``generate_employee_id`` utility method can be used to generate a new employee ID when
a new employee record is being added to the database.
"""

from __future__ import annotations
from sqlalchemy import func
from server.lib.logging_manager import LoggingManager
from server.lib.service_manager import SharedData
from server.lib.error_codes import ERR_DB_SERVICE_INACTIVE
from sqlalchemy.exc import SQLAlchemyError
from server.lib.data_classes.employee import Employee
from passlib.hash import bcrypt
from server.lib.strings import LOG_ERROR_GENERAL


def generate_employee_id(first_name: str, last_name: str) -> str | None:
    """
    This utility method is used to generate an employee ID from the given first name and last name.
    The ID format for employees is: ``<first_name_initial><full_last_name><unique_record_id>``

    :param first_name: The first name of the employee.
    :type first_name: str, required
    :param last_name: The last name of the employee.
    :type last_name: str, required
    :return: The newly created employee ID if successful, otherwise None.
    :rtype: str | None
    """
    # Get the instance of the application shared data and ensure the database engine is initialized.
    shared_data = SharedData()
    if not shared_data.Managers.get_database_manager().db_engine:
        raise RuntimeError(f'Database Error [Error Code: {ERR_DB_SERVICE_INACTIVE}]\n'
                           'The database was unable to be verified as online and active!')
    # Ensure that the provided first and last names are a valid length.
    if not len(first_name) > 0 and not len(last_name) > 0:
        return None
    try:
        with shared_data.Managers.get_database_manager().make_session() as session:
            # Query the last record with the highest ID that was inserted into the database to calculate the employee's new unique record ID.
            highest_id = session.query(func.max(Employee.id)).scalar()
            if highest_id is None:
                blank_employee = Employee("ID00", "BlankEmployee", "BlankEmployee", create_employee_password_hashes("BlankPassword"), enabled=False)
                session.add(blank_employee)
                session.flush()
                highest_id = blank_employee.id
            # Generate the ID using the first name, last name, and unique record ID.
            new_employee_id = f"{first_name[0].lower()}{last_name.lower()}{highest_id+1}"
    except SQLAlchemyError as err:
        LoggingManager.log(LoggingManager.LogLevel.LOG_CRITICAL, f"Error: {str(err)}", origin=LOG_ERROR_GENERAL, no_print=False)
        return None
    return new_employee_id


def create_employee_password_hashes(password: str) -> str | None:
    """
    This utility method creates a hashed and salted digest of a provided plain text password using BCrypt.

    :param password: The plain text password that needs the hash and salt generated.
    :type password: str, required
    :return: the newly generated employee password hash if successful, or None if the provided parameters are invalid.
    :rtype: str | None
    """
    if password is None or len(password) == 0:
        return None
    employee_password_hash = bcrypt.hash(password.encode('utf-8'))
    return employee_password_hash


def verify_employee_password(plain_password: str, password_hash: str) -> bool | None:
    """
    This utility method verifies that the provided plain text password when hashed and salted is equal
    to the provided password hash. A password that is hashed and equal to the provided hashed password
    proves that the password provided by the user is the correct password.
    Authentication can be granted to the user upon succeeding this verification.

    :param plain_password: The plain text password that needs to be verified.
    :type plain_password: str, required
    :param password_hash: The hashed password from the database that is compared to the hash of the plain text password.
    :type password_hash: str, required
    :return: True if the password is correct, False if it is incorrect, or None if the provided parameters are invalid.
    :rtype: bool | None
    """
    if None in (plain_password, password_hash) or len(plain_password) == 0 or len(password_hash) == 0:
        return None
    verify_key = bcrypt.verify(plain_password.encode('utf-8'), password_hash)
    return verify_key
