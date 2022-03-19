from __future__ import annotations
from typing import Dict, List
from server.lib.database_manager import get_db_session
from server.lib.data_classes.contact_info import ContactInfo
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
    pyd_student.parent_full_name = pyd_student.parent_full_name.lower().strip()
    pyd_student.parent_primary_email = pyd_student.parent_primary_email.lower().strip()
    if pyd_student.parent_secondary_email:
        pyd_student.parent_secondary_email = pyd_student.parent_secondary_email.lower().strip()
    if pyd_student.enable_notifications is None:
        pyd_student.enable_notifications = True
    if pyd_student.is_enabled is None:
        pyd_student.is_enabled = True

    if len(pyd_student.first_name) == 0 or len(pyd_student.last_name) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The first and last name of the student must not be empty!")
    if len(pyd_student.parent_full_name) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The full name for the point of contact cannot be empty!")
    if len(pyd_student.parent_primary_email) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The primary email must not be empty!")
    if pyd_student.car_pool_number < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The car pool number cannot be a negative number!")

    # Create student ID.
    student_id = await generate_student_id(pyd_student.first_name, pyd_student.last_name, pyd_student.car_pool_number, session)
    if student_id is None:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The student first name, last name, or car pool number is invalid and cannot be used to create a student ID!")

    # Create student contact information.
    contact_info = ContactInfo(student_id, pyd_student.parent_full_name, pyd_student.parent_primary_email, pyd_student.parent_secondary_email, pyd_student.enable_notifications)
    if contact_info is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The contact information for the student could not be created due to invalid parameters!")
    session.add(contact_info)
    session.flush()

    # Create the student and add it to the database.
    try:
        new_student = Student(student_id, pyd_student.first_name, pyd_student.last_name, contact_info.id, pyd_student.is_enabled)
        session.add(new_student)
        session.commit()
    except IntegrityError as err:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    # Retrieve the created student from the database to ensure it has been properly added.
    created_student = session.query(Student).filter(Student.StudentID == student_id).one()
    created_student = created_student.as_detail_dict()
    # Add contact information elements into response for the web interface.
    created_student['parent_full_name'] = contact_info.FullNameOfContact
    created_student['parent_primary_email'] = contact_info.PrimaryEmail
    created_student['parent_secondary_email'] = contact_info.SecondaryEmail
    created_student['email_notifications_enabled'] = contact_info.EnableNotifications
    # Remove unnecessary elements from response for the web interface.
    del created_student['entry_created']
    del created_student['contact_id']
    return created_student


async def update_students(student_updates: Dict[str, PydanticStudentUpdate], session: Session = None) -> List[Student]:
    if student_updates is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provided request body did not contain any valid employee information!")
    all_updated_students: List[Student] = []
    for student_id in student_updates.keys():
        updated_student = await update_student(student_id, student_updates[student_id], session)
        all_updated_students.append(updated_student)
    if len(student_updates) != len(all_updated_students):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more students were not able to be updated!")
    return all_updated_students


async def update_student(student_id: str, pyd_student_update: PydanticStudentUpdate, session: Session = None) -> Student:
    if pyd_student_update is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provided request body did not contain any valid employee information!")
    if student_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The student ID must be provided to update student information!")

    # Get student information from the database.
    student = session.query(Student).filter(Student.StudentID == student_id).first()
    if student is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The student ID is incorrect or the student does not exist!")
    student_contact_info = session.query(ContactInfo).filter(ContactInfo.id == student.ContactInfoID).first()
    if student_contact_info is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The student does not have contact information registered, please do that first!")

    # Check to see what data was provided and update as necessary.
    if pyd_student_update.first_name:
        student.FirstName = pyd_student_update.first_name.lower().strip()
    if pyd_student_update.last_name:
        student.LastName = pyd_student_update.last_name.lower().strip()
    if pyd_student_update.parent_primary_email:
        student_contact_info.PrimaryEmail = pyd_student_update.parent_primary_email.lower().strip()
        student_contact_info.LastUpdated = None
    if pyd_student_update.parent_secondary_email:
        student_contact_info.SecondaryEmail = pyd_student_update.parent_secondary_email.lower().strip()
        student_contact_info.LastUpdated = None
    if pyd_student_update.enable_notifications:
        student_contact_info.EnableNotifications = pyd_student_update.enable_notifications
        student_contact_info.LastUpdated = None
    if pyd_student_update.is_enabled:
        student_contact_info.EmployeeEnabled = pyd_student_update.is_enabled
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


async def get_student_contact_info(student: Student, session: Session = None) -> ContactInfo:
    if student is None:
        raise RuntimeError('The student object was not provided! Please check for errors in the provided data!')
    if session is None:
        session = next(get_db_session())
    matching_contact = session.query(ContactInfo).filter(
        student.ContactInfoID == ContactInfo.id
    ).first()
    if matching_contact is None:
        raise RuntimeError('The student contact information was not found using the student entity. Please check for errors in the database or the provided data!')
    return matching_contact


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
