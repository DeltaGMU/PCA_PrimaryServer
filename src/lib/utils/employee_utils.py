from __future__ import annotations
from sqlalchemy import func
from src.lib.logging_manager import LoggingManager
from src.lib.service_manager import SharedData
from src.lib.error_codes import ERR_DB_SRVCE_INACTIVE
from sqlalchemy.exc import SQLAlchemyError
from src.lib.data_classes.employee import Employee
from passlib.hash import bcrypt
from src.lib.strings import LOG_ERROR_GENERAL


def generate_employee_id(first_name: str, last_name: str) -> str | None:
    shared_data = SharedData()
    if not shared_data.Managers.get_database_manager().db_engine:
        raise RuntimeError(f'Database Error [Error Code: {ERR_DB_SRVCE_INACTIVE}]\n'
                           'The database was unable to be verified as online and active!')
    if not len(first_name) > 0 and not len(last_name) > 0:
        return None
    try:
        with shared_data.Managers.get_database_manager().make_session() as session:
            highest_id = session.query(func.max(Employee.id)).scalar()
            if highest_id is None:
                blank_employee = Employee("ID00", "BlankEmployee", "BlankEmployee", create_employee_password_hashes("BlankPassword"), enabled=False)
                session.add(blank_employee)
                session.flush()
                highest_id = blank_employee.id
            new_employee_id = f"PCA{first_name[0].upper()}{last_name[0].upper()}{highest_id+1}"
    except SQLAlchemyError as err:
        LoggingManager.log(LoggingManager.LogLevel.LOG_CRITICAL, f"Error: {str(err)}", origin=LOG_ERROR_GENERAL, no_print=False)
        return None
    return new_employee_id


def create_employee_password_hashes(password: str) -> (bytes, bytes):
    employee_password_hash = bcrypt.hash(password.encode('utf-8'))

    # employee_password_salt = urandom(32)
    # employee_password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'),
    #                                             employee_password_salt, 100000, dklen=128)
    return employee_password_hash


def verify_employee_password(plain_password: str, password_hash: str) -> bool:
    # verify_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), employee.PasswordSalt, 100000, dklen=128)
    verify_key = bcrypt.verify(plain_password.encode('utf-8'), password_hash)
    return verify_key
