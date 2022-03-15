"""
The student utility module contains multiple utility methods that serve to help student-related tasks.
For example, the ``generate_student_id`` utility method can be used to generate a new student ID when
a new student record is being added to the database.
"""

from __future__ import annotations
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from server.lib.data_classes.student import Student
from server.lib.logging_manager import LoggingManager
from server.lib.database_manager import get_db_session
from server.lib.strings import LOG_ERROR_DATABASE, LOG_ERROR_GENERAL, LOG_ORIGIN_GENERAL


def generate_student_id(first_name: str, last_name: str, carpool_number: int, session: Session = None) -> str:
    """
    This utility method is used to generate a student ID from the given first name and last name.
    The ID format for students is: ``<first_name_initial><full_last_name><unique_record_id>``

    :param first_name: The first name of the student.
    :type first_name: str, required
    :param last_name: The last name of the student.
    :type last_name: str, required
    :param carpool_number: The carpool number that corresponds to the student.
    :type carpool_number: int, required
    :param session: The database session to use to create a unique student ID.
    :type session: sqlalchemy.orm.session, optional
    :return: The newly created student ID if successful, otherwise None.
    :rtype: str | None
    :raises RuntimeError: If any of the provided parameters are invalid, or there was a database issue with querying for student IDs.
    """
    if session is None:
        session = next(get_db_session())
    if None in (first_name, last_name, carpool_number):
        LoggingManager().log(LoggingManager.LogLevel.LOG_CRITICAL, f"One or more provided parameters to generate the student ID was invalid!",
                             error_type=LOG_ORIGIN_GENERAL, origin=LOG_ORIGIN_GENERAL, no_print=False)
        raise RuntimeError(f'One or more provided parameters to generate the student ID was invalid!')
    new_student_id = f"{first_name[0].lower()}{last_name.lower()}{carpool_number}"
    student_id_duplicate_counter = 1
    try:
        student_id_exists = session.query(Student).filter(Student.StudentID == new_student_id).first()
        while student_id_exists:
            new_student_id = f"{first_name[0].lower()}{last_name.lower()}{carpool_number}{student_id_duplicate_counter}"
            student_id_duplicate_counter += 1
            student_id_exists = session.query(Student).filter(Student.StudentID == new_student_id).first()
    except SQLAlchemyError as err:
        LoggingManager().log(LoggingManager.LogLevel.LOG_CRITICAL, f"Encountered an error creating a unique student ID: {str(err)}",
                             error_type=LOG_ERROR_DATABASE, origin=LOG_ERROR_DATABASE, no_print=False)
        raise RuntimeError("Encountered an error creating a unique student ID!") from err
    LoggingManager().log(LoggingManager.LogLevel.LOG_INFO, f"Generated a new unique student ID.",
                         origin=LOG_ORIGIN_GENERAL, no_print=False)
    return new_student_id
