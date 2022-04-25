"""
This module contains the functions that interface with the database server
to handle the processing of student grade levels. Any code related to the handling of
student grade level records that require creating, reading, updating, or deleting data from the database server
must use this interface module.
"""
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from server.lib.logging_manager import LoggingManager
from server.lib.strings import LOG_ORIGIN_API
from server.lib.data_models.student import Student
from server.lib.data_models.student_grade import StudentGrade, PydanticStudentGrade
from server.lib.database_manager import get_db_session


async def retrieve_all_grades(session: Session = None) -> List[StudentGrade]:
    """
    This method is used to retrieve all the student grade levels stored in the database.

    :param session: The database session used to retrieve all the student grade levels.
    :type session: Session, optional
    :return: A list of all the student grade levels.
    :rtype: List[StudentGrade]
    """
    if session is None:
        session = next(get_db_session())
    all_grades = session.query(StudentGrade).all()
    return all_grades


async def retrieve_one_grade(grade_name: str, session: Session = None) -> StudentGrade:
    """
    This method is used to retrieve a single grade level record from the database provided the name of the grade level.

    :param grade_name: The name of the student grade level to retrieve from the database.
    :type grade_name: str, required
    :param session: The database session used to retrieve a student grade level record from the database.
    :type session: Session, optional
    :return: A student grade level record
    :rtype: StudentGrade
    :raises HTTPException: If any of the provided parameters is invalid, or the student grade level does not exist.
    """
    if grade_name is None or len(grade_name) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The provided student grade is invalid or empty!")
    if session is None:
        session = next(get_db_session())
    grade_name = grade_name.lower().strip()
    matching_grade = session.query(StudentGrade).filter(
        StudentGrade.Name == grade_name
    ).first()
    if matching_grade is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The student grade record does not exist!")
    return matching_grade


async def create_student_grade(student_grade: PydanticStudentGrade, session: Session = None) -> StudentGrade:
    """
    This method is used to create a new student grade level record from the provided grade name.

    :param student_grade: The name of the student grade level that should be added to the database.
    :type student_grade: PydanticStudentGrade, required
    :param session: The database session used to create a new student grade record.
    :type session: Session, optional
    :return: The student grade level record
    :rtype: StudentGrade
    :raises HTTPException: If any of the parameters are invalid, or the student grade level already exists.
    """
    student_grade = student_grade.student_grade
    if len(student_grade) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The student grade name cannot be empty!")
    if session is None:
        session = next(get_db_session())
    student_grade = student_grade.lower().strip()
    grade_exists = session.query(StudentGrade).filter(StudentGrade.Name == student_grade).first()
    if grade_exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"The student grade: '{student_grade}' already exists!")
    try:
        new_student_grade = StudentGrade(student_grade)
        session.add(new_student_grade)
        session.commit()
        LoggingManager().log(LoggingManager.LogLevel.LOG_INFO,
                             f"A new student grade level: {new_student_grade.Name} has been created.",
                             origin=LOG_ORIGIN_API, no_print=False)
    except IntegrityError as err:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return new_student_grade


async def remove_student_grade(student_grade: PydanticStudentGrade, session: Session = None) -> StudentGrade:
    """
    This method is used to remove an existing student grade level from the database from the student grade name.
    Please note that a student grade level that is currently used by a student cannot be deleted.

    :param student_grade: The name of the student grade of the student grade level record that should be removed.
    :type student_grade: PydanticStudentGrade, required
    :param session: The database session used to delete the existing student grade level record.
    :type session: Session, optional
    :return: The student grade level record that was removed from the database.
    :rtype: StudentGrade
    :raises HTTPException: If any of the provided parameters are invalid, or the student grade level to be deleted does not exist or the grade level is currently in use.
    """
    student_grade = student_grade.student_grade.lower().strip()
    if len(student_grade) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The student grade name cannot be empty!")
    if session is None:
        session = next(get_db_session())
    try:
        matching_grade = session.query(StudentGrade).filter(StudentGrade.Name == student_grade).first()
        if matching_grade is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The provided student grade does not exist!")
        check_students = session.query(Student, StudentGrade).filter(
            Student.StudentID == StudentGrade.id,
            StudentGrade.Name == student_grade
        ).all()
        if len(check_students) > 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove a student grade that is currently in use!")
        session.delete(matching_grade)
        session.commit()
        LoggingManager().log(LoggingManager.LogLevel.LOG_INFO,
                             f"A student grade level: {matching_grade.Name} has been deleted.",
                             origin=LOG_ORIGIN_API, no_print=False)
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove a student grade that is currently in use!")
    except SQLAlchemyError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return matching_grade
