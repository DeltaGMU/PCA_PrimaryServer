from __future__ import annotations
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from src.lib.data_classes.student import Student
from src.lib.error_codes import ERR_DB_SRVCE_INACTIVE
from src.lib.logging_manager import LoggingManager
from src.lib.service_manager import SharedData
from src.lib.strings import LOG_ERROR_GENERAL


def generate_student_id(first_name: str, last_name: str) -> str | None:
    shared_data = SharedData()
    if not shared_data.Managers.get_database_manager().db_engine:
        raise RuntimeError(f'Database Error [Error Code: {ERR_DB_SRVCE_INACTIVE}]\n'
                           'The database was unable to be verified as online and active!')
    if not len(first_name) > 0 and not len(last_name) > 0:
        return None
    try:
        with shared_data.Managers.get_database_manager().make_session() as session:
            highest_id = session.query(func.max(Student.id)).scalar()
            if highest_id is None:
                blank_student = Student("IDSTUDENT00", "BlankStudent", "BlankStudent", enabled=False)
                session.add(blank_student)
                session.flush()
                highest_id = blank_student.id
            new_student_id = f"ID{first_name[0].upper()}{last_name[0].upper()}{highest_id+1}"
    except SQLAlchemyError as err:
        LoggingManager.log(LoggingManager.LogLevel.LOG_CRITICAL, f"Error: {str(err)}", origin=LOG_ERROR_GENERAL, no_print=False)
        return None
    return new_student_id
