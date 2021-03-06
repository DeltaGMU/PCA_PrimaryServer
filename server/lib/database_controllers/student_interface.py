"""
This module contains the functions that interface with the database server
to handle the processing of student records. Any code related to the handling of
student records that require creating, reading, updating, or deleting data from the database server
must use this interface module.
"""

from __future__ import annotations
from typing import Dict, List

from server.lib.logging_manager import LoggingManager
from server.lib.strings import LOG_ORIGIN_API
from server.lib.data_models.student_care_hours import StudentCareHours
from server.lib.utils.email_utils import send_email
from server.lib.data_models.student_grade import StudentGrade
from server.lib.database_manager import get_db_session
from server.lib.data_models.student_contact_info import StudentContactInfo
from server.lib.utils.student_utils import generate_student_id
from server.lib.data_models.student import PydanticStudentRegistration, Student, PydanticStudentUpdate, PydanticStudentsRemoval
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import sql
from fastapi import HTTPException, status


async def create_student(pyd_student: PydanticStudentRegistration, session: Session = None) -> Dict[str, any]:
    """
    This method creates a new student record with all associated student information such as
    parent contact information and student grade level, and inserts the records into the database.
    When a new student record is created, an email is automatically sent to the primary parent email notifying them
    that their child's account has been set up.

    :param pyd_student: The set of information required to register a new student record, represented by the ``PydanticStudentRegistration`` pydantic class.
    :type pyd_student: PydanticStudentRegistration, required
    :param session: The database session used to insert the student information into the database.
    :type session: Session, optional
    :return: A JSON-Compatible dictionary containing the newly created student record information.
    :rtype: Dict[str, any]
    :raises HTTPException: If any of the provided parameters are invalid, or a database error occurred during student creation.
    """

    if session is None:
        session = next(get_db_session())

    pyd_student.first_name = pyd_student.first_name.lower().strip()
    pyd_student.last_name = pyd_student.last_name.lower().strip()
    pyd_student.parent_one_first_name = pyd_student.parent_one_first_name.lower().strip()
    pyd_student.parent_one_last_name = pyd_student.parent_one_last_name.lower().strip()
    if pyd_student.parent_two_first_name:
        pyd_student.parent_two_first_name = pyd_student.parent_two_first_name.lower().strip()
    if pyd_student.parent_two_last_name:
        pyd_student.parent_two_last_name = pyd_student.parent_two_last_name.lower().strip()
    pyd_student.primary_email = pyd_student.primary_email.lower().strip()
    pyd_student.grade = pyd_student.grade.lower().strip()
    if pyd_student.secondary_email:
        pyd_student.secondary_email = pyd_student.secondary_email.lower().strip()
    if pyd_student.enable_primary_email_notifications is None:
        pyd_student.enable_primary_email_notifications = True
    if pyd_student.enable_secondary_email_notifications is None:
        pyd_student.enable_secondary_email_notifications = False
    if pyd_student.is_enabled is None:
        pyd_student.is_enabled = True

    if len(pyd_student.first_name) == 0 or len(pyd_student.last_name) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The first and last name of the student must not be empty!")
    if len(pyd_student.parent_one_first_name) == 0 or len(pyd_student.parent_one_last_name) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parent #1 first and last names cannot be empty!")
    if len(pyd_student.primary_email) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The primary email must not be empty!")
    if pyd_student.car_pool_number < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The car pool number cannot be a negative number!")

    # Create student ID.
    student_id = await generate_student_id(pyd_student.first_name, pyd_student.last_name, pyd_student.car_pool_number, session)
    if student_id is None:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The student first name, last name, or car pool number is invalid and cannot be used to create a student ID!")

    # Create student contact information.
    contact_info = StudentContactInfo(student_id,
                                      pyd_student.parent_one_first_name,
                                      pyd_student.parent_one_last_name,
                                      pyd_student.primary_email,
                                      pyd_student.parent_two_first_name,
                                      pyd_student.parent_two_last_name,
                                      pyd_student.secondary_email,
                                      pyd_student.enable_primary_email_notifications,
                                      pyd_student.enable_secondary_email_notifications)
    if contact_info is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The contact information for the student could not be created due to invalid parameters!")

    # Verify that the student grade is valid and return the grade id for the specified grade.
    grade_query = session.query(StudentGrade).filter(StudentGrade.Name == pyd_student.grade).first()
    if not grade_query:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The provided student grade is invalid or does not exist!")

    # Create the student and add it to the database.
    try:
        new_student = Student(student_id, pyd_student.first_name, pyd_student.last_name, pyd_student.car_pool_number,
                              contact_info, grade_query.id, pyd_student.is_enabled)
        session.add(new_student)
        session.commit()
        LoggingManager().log(LoggingManager.LogLevel.LOG_INFO,
                             f"A new student account record was created: {new_student.StudentID}.",
                             origin=LOG_ORIGIN_API, no_print=False)
        LoggingManager().log(LoggingManager.LogLevel.LOG_INFO,
                             f"A new student contact information record was created for {new_student.StudentID}.",
                             origin=LOG_ORIGIN_API, no_print=False)
    except IntegrityError as err:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    # Send notification to enabled emails that the account has been created.
    if new_student.StudentContactInfo.EnablePrimaryEmailNotifications:
        send_email(
            to_user=f'{new_student.StudentContactInfo.ParentOneFirstName} {new_student.StudentContactInfo.ParentOneLastName}',
            to_email=[new_student.StudentContactInfo.PrimaryEmail],
            subj="New Student Registration Confirmed",
            messages=["Your student's account has been created!",
                      "Your student's information is provided below:",
                      f"<b>Student Name:</b> {new_student.FirstName.title()} {new_student.LastName.title()}",
                      f"<b>Student ID:</b> {new_student.StudentID}",
                      "<b>Please remember the Student ID as this will be used to check-in/check-out your student from before/after-care services.</b>",
                      "If any of the information provided is incorrect, please contact PCA administration to make corrections."]
        )
    if new_student.StudentContactInfo.EnableSecondaryEmailNotifications:
        send_email(
            to_user=f'{new_student.StudentContactInfo.ParentTwoFirstName} {new_student.StudentContactInfo.ParentTwoLastName}',
            to_email=[new_student.StudentContactInfo.SecondaryEmail],
            subj="New Student Registration Confirmed",
            messages=["Your student's account has been created!",
                      "Your student's information is provided below:",
                      f"<b>Student Name:</b> {new_student.FirstName.title()} {new_student.LastName.title()}",
                      f"<b>Student ID:</b> {new_student.StudentID}",
                      "<b>Please remember the Student ID as this will be used to check-in/check-out your student from before/after-care services.</b>",
                      "If any of the information provided is incorrect, please contact PCA administration to make corrections."]
        )
    return new_student.as_dict()


async def update_students(student_updates: Dict[str, PydanticStudentUpdate], session: Session = None) -> List[Student]:
    """
    This method updates one or more student records with updated student information provided in the form
    of a dictionary consisting of student ID keys and student update information values. Upon successful
    submission of a student record, an email is sent to the student's parents notifying them that their child's account has been updated.

    :param student_updates: A dictionary containing student update information values paired with student ID keys.
    :type student_updates: Dict[str, PydanticStudentUpdate]
    :param session: The database session used to update one or more student records.
    :type session: Session, optional
    :return: A list of the student records that have been updated in the database.
    :rtype: List[Student]
    :raises HTTPException: If any of the provided parameters are invalid.
    """
    if student_updates is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provided request body did not contain any valid student information!")
    all_updated_students: List[Student] = []
    for student_id in student_updates.keys():
        updated_student = await update_student(student_id, student_updates[student_id], session)
        all_updated_students.append(updated_student)
    if len(student_updates) != len(all_updated_students):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more students were not able to be updated!")
    LoggingManager().log(LoggingManager.LogLevel.LOG_INFO,
                         f"The following student account records were updated: {','.join([student.StudentID for student in all_updated_students])}.",
                         origin=LOG_ORIGIN_API, no_print=False)
    return all_updated_students


async def update_student(student_id: str, pyd_student_update: PydanticStudentUpdate, session: Session = None) -> Student:
    """
    This method updates a single student record with updated student information.
    Upon successful submission of the student record, an email is sent to the student's parents notifying
    them that their child's account has been updated.

    :param student_id: The ID of the student.
    :type student_id: str, required
    :param pyd_student_update: The updated student information that should be used.
    :type pyd_student_update: PydanticStudentUpdate, required
    :param session: The database session used to update the student record.
    :type session: Session, optional
    :return: The student record that has been updated.
    :rtype: Employee
    """
    if pyd_student_update is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provided request body did not contain any valid student information!")
    if student_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The student ID must be provided to update student information!")

    # Get student information from the database.
    student = session.query(Student).filter(Student.StudentID == student_id).first()
    if student is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The student ID is incorrect or the student does not exist!")
    student_contact_info = student.StudentContactInfo
    if student_contact_info is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The student does not have contact information registered, please do that first!")
    student_grade_info = session.query(StudentGrade).filter(StudentGrade.id == student.GradeID).first()
    if student_grade_info is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The student does not have a student grade registered, please do that first!")

    # Check to see what data was provided and update as necessary.
    if pyd_student_update.first_name is not None:
        student.FirstName = pyd_student_update.first_name.lower().strip()
        student.LastUpdated = sql.func.now()
    if pyd_student_update.last_name is not None:
        student.LastName = pyd_student_update.last_name.lower().strip()
        student.LastUpdated = sql.func.now()
    if pyd_student_update.car_pool_number is not None:
        if pyd_student_update.car_pool_number >= 0:
            student.CarpoolNumber = pyd_student_update.car_pool_number
            student.LastUpdated = sql.func.now()
    if pyd_student_update.parent_one_first_name is not None:
        student_contact_info.ParentOneFirstName = pyd_student_update.parent_one_first_name.lower().strip()
        student_contact_info.LastUpdated = sql.func.now()
    if pyd_student_update.parent_one_last_name is not None:
        student_contact_info.ParentOneLastName = pyd_student_update.parent_one_last_name.lower().strip()
        student_contact_info.LastUpdated = sql.func.now()
    if pyd_student_update.parent_two_first_name is not None:
        student_contact_info.ParentTwoFirstName = pyd_student_update.parent_two_first_name.lower().strip()
        student_contact_info.LastUpdated = sql.func.now()
    if pyd_student_update.parent_two_last_name is not None:
        student_contact_info.ParentTwoLastName = pyd_student_update.parent_two_last_name.lower().strip()
        student_contact_info.LastUpdated = sql.func.now()
    if pyd_student_update.primary_email is not None:
        student_contact_info.PrimaryEmail = pyd_student_update.primary_email.lower().strip()
        student_contact_info.LastUpdated = sql.func.now()
    if pyd_student_update.secondary_email is not None:
        student_contact_info.SecondaryEmail = pyd_student_update.secondary_email.lower().strip()
        student_contact_info.LastUpdated = sql.func.now()
    else:
        student_contact_info.SecondaryEmail = None
        student_contact_info.EnableSecondaryEmailNotifications = False
        student_contact_info.LastUpdated = sql.func.now()
    if pyd_student_update.enable_primary_email_notifications is not None:
        student_contact_info.EnablePrimaryEmailNotifications = pyd_student_update.enable_primary_email_notifications
        student_contact_info.LastUpdated = sql.func.now()
    if pyd_student_update.enable_secondary_email_notifications is not None:
        student_contact_info.EnableSecondaryEmailNotifications = pyd_student_update.enable_secondary_email_notifications
        student_contact_info.LastUpdated = sql.func.now()
    if pyd_student_update.is_enabled is not None:
        student.StudentEnabled = pyd_student_update.is_enabled
        student.LastUpdated = sql.func.now()
    if pyd_student_update.grade:
        grade_query = session.query(StudentGrade).filter(StudentGrade.Name == pyd_student_update.grade.lower().strip()).first()
        if not grade_query:
            session.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The provided student grade is invalid or does not exist!")
        student.GradeID = grade_query.id
        student.LastUpdated = sql.func.now()
    session.commit()
    LoggingManager().log(LoggingManager.LogLevel.LOG_INFO,
                         f"The following student account had its information updated: {student.StudentID}.",
                         origin=LOG_ORIGIN_API, no_print=False)
    # Send notification to enabled emails that the account has been created.
    if student.StudentContactInfo.EnablePrimaryEmailNotifications:
        send_email(
            to_user=f'{student.StudentContactInfo.ParentOneFirstName} {student.StudentContactInfo.ParentOneLastName}',
            to_email=[student.StudentContactInfo.PrimaryEmail],
            subj="Student Account Information Has Been Updated!",
            messages=[
                "Your student's account information has been updated!",
                "If you're not aware of updates to your student's account, please contact an administrator for more information."
            ],
        )
    if student.StudentContactInfo.EnableSecondaryEmailNotifications:
        send_email(
            to_user=f'{student.StudentContactInfo.ParentTwoFirstName} {student.StudentContactInfo.ParentTwoLastName}',
            to_email=[student.StudentContactInfo.SecondaryEmail],
            subj="Student Account Information Has Been Updated!",
            messages=[
                "Your student's account information has been updated!",
                "If you're not aware of updates to your student's account, please contact an administrator for more information."
            ],
        )
    return student


async def check_student_has_records(student_id: str, session: Session = None) -> bool:
    """
    This utility method is used to check if a student record has any associated student care service records.

    :param student_id: The ID of the student.
    :type student_id: str, required
    :param session: The database session used to retrieve student care records.
    :type session: Session, optional
    :return: True if the student has associated student care service records.
    :rtype: bool
    :raises HTTPException: If the provided student ID is invalid.
    """
    if session is None:
        session = next(get_db_session())
    if student_id is None or not isinstance(student_id, str):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The provided student ID is invalid!")
    matching_student = session.query(Student).filter(
        Student.StudentID == student_id.strip()
    ).first()
    student_has_records = session.query(StudentCareHours).filter(
        matching_student.StudentID == StudentCareHours.StudentID,
    ).all()
    if len(student_has_records) > 0:
        return True
    return False


async def get_student_by_id(student_id: str, session: Session = None) -> Student:
    """
    This utility method is used to retrieve a student record from the provided student ID.

    :param student_id: The ID of the student.
    :type student_id: str, required
    :param session: The database session used to retrieve the student record.
    :type session: Session, optional
    :return: The student record retrieved from the database.
    :rtype: Student
    :raises HTTPException: If the student ID is invalid, or the student record does not exist.
    """
    if session is None:
        session = next(get_db_session())

    student_id = student_id.strip().lower()
    if len(student_id) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='The student ID provided to the utility method to retrieve student information is invalid due to an ID length of 0!')

    matching_student = session.query(Student).filter(
        Student.StudentID == student_id
    ).first()
    if matching_student is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='The student was not found by the provided ID. Please check for errors in the provided data!')
    return matching_student


async def get_student_contact_info(student_id: str, session: Session = None) -> StudentContactInfo:
    """
    This method is used to retrieve a student record's parent contact information.

    :param student_id: The ID of the student.
    :type student_id: str, required
    :param session: The database session used to retrieve the student's parent contact information.
    :type session: Session, optional
    :return: The student's parent contact information associated with the provided employee ID.
    :rtype: StudentContactInfo
    :raises RuntimeError: If the student ID is null or if there is no parent contact information associated with the student record.
    """
    if student_id is None:
        raise RuntimeError('The student ID was not provided! Please check for errors in the provided data!')
    student_id = student_id.lower().strip()
    if session is None:
        session = next(get_db_session())
    matching_student = session.query(Student).filter(
        Student.StudentID == student_id
    ).first()
    contact_info = matching_student.StudentContactInfo
    if contact_info is None:
        raise RuntimeError('The student contact information was not found using the student ID. Please check for errors in the database or the provided data!')
    return contact_info


async def get_student_grade(student: Student, session: Session = None) -> StudentGrade:
    """
    This method is used to retrieve the grade level of the provided student record.

    :param student: The student record used to retrieve the grade level of the provided student record.
    :type student: Student
    :param session: The database session used to retrieve the student grade level.
    :type session: Session, optional
    :return: The student grade level of the provided student record.
    :rtype: StudentGrade
    :raises RuntimeError: If the student record is null, or the student grade level is invalid or doesn't exist in the database.
    """
    if student is None:
        raise RuntimeError('The student object was not provided! Please check for errors in the provided data!')
    if session is None:
        session = next(get_db_session())
    matching_grade = session.query(StudentGrade).filter(
        student.GradeID == StudentGrade.id
    ).first()
    if matching_grade is None:
        raise RuntimeError('The student grade information was not found using the student entity. Please check for errors in the database or the provided data!')
    return matching_grade


async def remove_students(student_ids: PydanticStudentsRemoval | str, session: Session = None) -> List[Student]:
    """
    This method accepts one or more student IDs and deletes the corresponding student records from the database.
    Please note that student records that have associated student care service records cannot be deleted unless all
    student care service records are removed.

    :param student_ids: A single student ID or a list of student IDs to delete the corresponding student record(s).
    :type student_ids: PydanticStudentsRemoval | str, required
    :param session: The database session used to delete one or more student records.
    :type session: Session, optional
    :return: The list of student records that have been deleted from the database.
    :rtype: List[Student]
    :raises HTTPException: If any of the provided parameters are invalid, or the student has associated student care service records.
    """
    if isinstance(student_ids, PydanticStudentsRemoval):
        student_ids = student_ids.student_ids
        if student_ids is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provided request body did not contain valid student IDs!")
    removed_students: List[Student] = []
    if isinstance(student_ids, List):
        students = session.query(Student).filter(Student.StudentID.in_(student_ids)).all()
        if students:
            for student in students:
                if not check_student_has_records(student.StudentID):
                    session.delete(student)
                    removed_students.append(student)
                else:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove a student with student care records!")
            session.commit()
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove students that do not exist in the database!")
    else:
        student = session.query(Student).filter(Student.StudentID == student_ids).first()
        if student:
            session.delete(student)
            removed_students.append(student)
            session.commit()
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove a student that does not exist in the database!")
    LoggingManager().log(LoggingManager.LogLevel.LOG_INFO,
                         f"The following student account records were deleted: {','.join([student.StudentID for student in removed_students])}.",
                         origin=LOG_ORIGIN_API, no_print=False)
    return removed_students
