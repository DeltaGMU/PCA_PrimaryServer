from typing import Dict

from server.lib.data_classes.contact_info import ContactInfo
from server.lib.utils.student_utils import generate_student_id
from server.lib.data_classes.student import PydanticStudentRegistration, Student
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status


async def create_student(pyd_student: PydanticStudentRegistration, session: Session = None) -> Dict[str, any]:
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
