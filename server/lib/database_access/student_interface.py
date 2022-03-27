from __future__ import annotations
from typing import Dict, List
from server.lib.data_classes.student_grade import StudentGrade
from server.lib.database_manager import get_db_session
from server.lib.data_classes.student_contact_info import StudentContactInfo
from server.lib.utils.student_utils import generate_student_id
from server.lib.data_classes.student import PydanticStudentRegistration, Student, PydanticStudentUpdate, PydanticStudentsRemoval
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status


async def create_student(pyd_student: PydanticStudentRegistration, session: Session = None) -> Dict[str, any]:
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
    # session.add(contact_info)
    # session.flush()

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
    except IntegrityError as err:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return new_student.as_dict()


async def update_students(student_updates: Dict[str, PydanticStudentUpdate], session: Session = None) -> List[Student]:
    if student_updates is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provided request body did not contain any valid student information!")
    all_updated_students: List[Student] = []
    for student_id in student_updates.keys():
        updated_student = await update_student(student_id, student_updates[student_id], session)
        all_updated_students.append(updated_student)
    if len(student_updates) != len(all_updated_students):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more students were not able to be updated!")
    return all_updated_students


async def update_student(student_id: str, pyd_student_update: PydanticStudentUpdate, session: Session = None) -> Student:
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
    if pyd_student_update.first_name:
        student.FirstName = pyd_student_update.first_name.lower().strip()
        student.LastUpdated = None
    if pyd_student_update.last_name:
        student.LastName = pyd_student_update.last_name.lower().strip()
        student.LastUpdated = None
    if pyd_student_update.parent_one_first_name:
        student_contact_info.ParentOneFirstName = pyd_student_update.parent_one_first_name.lower().strip()
        student_contact_info.LastUpdated = None
    if pyd_student_update.parent_one_last_name:
        student_contact_info.ParentOneLastName = pyd_student_update.parent_one_last_name.lower().strip()
        student_contact_info.LastUpdated = None
    if pyd_student_update.parent_two_first_name:
        student_contact_info.ParentTwoFirstName = pyd_student_update.parent_two_first_name.lower().strip()
        student_contact_info.LastUpdated = None
    if pyd_student_update.parent_two_last_name:
        student_contact_info.ParentTwoLastName = pyd_student_update.parent_two_last_name.lower().strip()
        student_contact_info.LastUpdated = None
    if pyd_student_update.parent_primary_email:
        student_contact_info.PrimaryEmail = pyd_student_update.primary_email.lower().strip()
        student_contact_info.LastUpdated = None
    if pyd_student_update.parent_secondary_email:
        student_contact_info.SecondaryEmail = pyd_student_update.secondary_email.lower().strip()
        student_contact_info.LastUpdated = None
    if pyd_student_update.enable_primary_email_notifications:
        student_contact_info.EnablePrimaryEmailNotifications = pyd_student_update.enable_primary_email_notifications
        student_contact_info.LastUpdated = None
    if pyd_student_update.enable_secondary_email_notifications:
        student_contact_info.EnableSecondaryEmailNotifications = pyd_student_update.enable_secondary_email_notifications
        student_contact_info.LastUpdated = None
    if pyd_student_update.is_enabled:
        student_contact_info.EmployeeEnabled = pyd_student_update.is_enabled
        student.LastUpdated = None
    if pyd_student_update.grade:
        grade_query = session.query(StudentGrade).filter(StudentGrade.Name == pyd_student_update.grade.lower().strip()).first()
        if not grade_query:
            session.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The provided student grade is invalid or does not exist!")
        student.GradeID = grade_query.id
        student.LastUpdated = None
    session.commit()
    return student


async def get_student_by_id(student_id: str, session: Session = None):
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
    if isinstance(student_ids, PydanticStudentsRemoval):
        student_ids = student_ids.student_ids
        if student_ids is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provided request body did not contain valid student IDs!")
    removed_students: List[Student] = []
    if isinstance(student_ids, List):
        students = session.query(Student).filter(Student.StudentID.in_(student_ids)).all()
        if students:
            for student in students:
                session.delete(student)
                removed_students.append(student)
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
    return removed_students
