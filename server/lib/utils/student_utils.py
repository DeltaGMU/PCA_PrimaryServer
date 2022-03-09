"""
The student utility module contains multiple utility methods that serve to help student-related tasks.
For example, the ``generate_student_id`` utility method can be used to generate a new student ID when
a new student record is being added to the database.
"""

from __future__ import annotations
from sqlalchemy.sql.expression import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from server.lib.data_classes.student import Student
from server.lib.error_codes import ERR_DB_SERVICE_INACTIVE
from server.lib.logging_manager import LoggingManager
from server.lib.database_manager import main_engine as db_engine, get_db_session
from server.lib.strings import LOG_ERROR_GENERAL


def generate_student_id(first_name: str, last_name: str, session: Session = None) -> str | None:
    """
    This utility method is used to generate a student ID from the given first name and last name.
    The ID format for students is: ``<first_name_initial><full_last_name><unique_record_id>``

    :param first_name: The first name of the student.
    :type first_name: str, required
    :param last_name: The last name of the student.
    :type last_name: str, required
    :param session: The database session to use to generate the student ID.
    :type session: Session, optional
    :return: The newly created student ID if successful, otherwise None.
    :rtype: str | None
    """
    if session is None:
        session = get_db_session()
    if db_engine is None:
        raise RuntimeError(f'Database Error [Error Code: {ERR_DB_SERVICE_INACTIVE}]\n'
                           'The database was unable to be verified as online and active!')
    if not len(first_name) > 0 and not len(last_name) > 0:
        return None
    try:
        highest_id = session.query(func.max(Student.id)).scalar()
        if highest_id is None:
            blank_student = Student("IDSTUDENT00", "BlankStudent", "BlankStudent", enabled=False)
            session.add(blank_student)
            session.flush()
            highest_id = blank_student.id
        new_student_id = f"{first_name[0].lower()}{last_name.lower()}{highest_id+1}"
    except SQLAlchemyError as err:
        LoggingManager.log(LoggingManager.LogLevel.LOG_CRITICAL, f"Error: {str(err)}", origin=LOG_ERROR_GENERAL, no_print=False)
        return None
    return new_student_id
