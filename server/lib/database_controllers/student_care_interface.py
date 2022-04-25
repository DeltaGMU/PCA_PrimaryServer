"""
This module contains the functions that interface with the database server
to handle the processing of student care service records. Any code related to the handling of
student care service records that require creating, reading, updating, or deleting data from the database server
must use this interface module.
"""
from __future__ import annotations
import time
from typing import Dict, List
from datetime import datetime, timedelta, date
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from fastapi import HTTPException, status

from server.lib.logging_manager import LoggingManager
from server.lib.strings import LOG_ORIGIN_API
from server.lib.utils.email_utils import send_email
from server.lib.data_models.student_grade import StudentGrade
from server.lib.config_manager import ConfigManager
from server.lib.data_models.student import Student
from server.lib.utils.date_utils import check_date_formats
from server.lib.data_models.student_care_hours import StudentCareHours, PydanticStudentCareHoursCheckOut, PydanticRetrieveCareStudentsByGrade, PydanticRetrieveStudentCareRecord, PydanticDeleteStudentCareRecord
from server.lib.data_models.student_care_hours import PydanticStudentCareHoursCheckIn
from server.lib.database_manager import get_db_session


async def get_care_timeslots() -> Dict[str, any]:
    """
    This utility method retrieves the before-care and after-care service timeslots from the server configuration file
    and returns the information as a JSON-Compatible dictionary.

    :return: Returns a JSON-Compatible dictionary containing the before-care and after-care service timeslots information.
    :rtype: Dict[str, any]
    """
    timeslots = {
        "metadata": {
            "before_care_check_in_time": ConfigManager().config()['Student Care Settings']['before_care_check_in_time'],
            "before_care_check_out_time": ConfigManager().config()['Student Care Settings']['before_care_check_out_time'],
            "after_care_check_in_time": ConfigManager().config()['Student Care Settings']['after_care_check_in_time'],
            "after_care_check_out_time": ConfigManager().config()['Student Care Settings']['after_care_check_out_time']
        }
    }
    return timeslots


async def get_one_student_care(student_id: str, care_date: str, session: Session = None) -> Dict[str, any] | None:
    """
    This method is used to retrieve before-care and after-care records for a student
    from the provided date. This is useful to determine if a student has participated in
    before-care or after-care for the day. If before-care or after-care records exist
    for the provided day, then the corresponding records are returned along with the care service timeslots.

    :param student_id: The ID of the student.
    :type student_id: str, required
    :param care_date: The date the student participated in a care service in YYYY-MM-DD format.
    :type care_date: str, required
    :param session: The database session used to retrieve student care records.
    :type session: Session, optional
    :return: None if no records exist, otherwise the student care timeslots and the before-care and after-care records for the student from the provided date if it exists is returned.
    :rtype: Dict[str, any] | None
    :raises HTTPException: If any of the provided parameters are invalid.
    """
    if session is None:
        session = next(get_db_session())
    if student_id is None or not isinstance(student_id, str):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The student ID must be a valid string!")
    if care_date is None or not check_date_formats(care_date):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The provided care service date must be valid! Ensure the date is in YYYY-MM-DD format!")
    student_id = student_id.lower().strip()
    student_care = session.query(StudentCareHours).filter(
        StudentCareHours.StudentID == student_id,
        StudentCareHours.CareDate == care_date
    ).all()
    if student_care is None:
        return None
    else:
        care_dict = await get_care_timeslots()
        for care in student_care:
            if not care.CareType:
                care_dict['before_care'] = care.as_dict()
            else:
                care_dict['after_care'] = care.as_dict()
        return care_dict


async def delete_student_care_records(pyd_student_care_delete: PydanticDeleteStudentCareRecord, session: Session = None):
    """
    This method is used to delete student care records for a single student by specifying either the care type and care date to delete either before-care or after-care,
    or only providing a care date to delete both before-care and after-care records for the provided date.

    :param pyd_student_care_delete: The ID of the student, care date, and optionally a care type (to delete specifically before-care or after-care)
    :type pyd_student_care_delete: PydanticDeleteStudentCareRecord, required
    :param session: The database session used to delete student care records from the database.
    :type session: Session, optional
    :return: None
    :rtype: None
    :raises HTTPException: If any of the provided parameters are invalid or the student ID does not exist.
    """
    if session is None:
        session = next(get_db_session())
    if None in (pyd_student_care_delete.student_id, pyd_student_care_delete.care_date):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A student ID and a care date must be provided!")
    if not check_date_formats(pyd_student_care_delete.care_date):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The care date provided was in an incorrect format! Ensure the date is in YYYY-MM-DD format!")

    student_exists = session.query(Student).filter(Student.StudentID == pyd_student_care_delete.student_id).first()
    if student_exists is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The provided student ID does not exist!")

    if pyd_student_care_delete.care_type is None:
        care_records = session.query(StudentCareHours).filter(
            StudentCareHours.StudentID == pyd_student_care_delete.student_id,
            StudentCareHours.CareDate == pyd_student_care_delete.care_date
        ).all()
    else:
        care_records = session.query(StudentCareHours).filter(
            StudentCareHours.StudentID == pyd_student_care_delete.student_id,
            StudentCareHours.CareDate == pyd_student_care_delete.care_date,
            StudentCareHours.CareType == pyd_student_care_delete.care_type
        ).all()
    for care_record in care_records:
        session.delete(care_record)
    session.commit()
    LoggingManager().log(LoggingManager.LogLevel.LOG_INFO,
                         f"One or more student care records have been deleted for: {pyd_student_care_delete.student_id}.",
                         origin=LOG_ORIGIN_API, no_print=False)


async def get_total_student_care_for_period(start_date: str, end_date: str, grade: str, session: Session = None):
    """
    This method retrieves the accumulated student care hours for before-care and after-care services
    for the provided range of dates for all students of the specified grade level.

    :param start_date: The start date of the student care records to retrieve in YYYY-MM-DD format.
    :type start_date: str, required
    :param end_date: The end date of the student care records to retrieve in YYYY-MM-DD format.
    :type end_date: str, required
    :param grade: The name of the student grade level to retrieve student records from.
    :type grade: str, required
    :param session: The database session used to retrieve student records and student care service records.
    :type session: Session, optional
    :return: A JSON-Compatible dictionary of accumulated student care hours for students of the specified grade over the provided range of dates.
    :rtype: Dict[str, any]
    :raises HTTPException: If any of the provided parameters are invalid or the student grade level doesn't exist.
    :raises RuntimeError: If an integrity error is encountered with the retrieval of database records.
    """
    if session is None:
        session = next(get_db_session())
    if not check_date_formats([start_date, end_date]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more provided dates are invalid! Please ensure the dates are provided in YYYY-MM-DD format.")
    if grade is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A student grade must be provided!")
    try:
        grade = grade.lower().strip()
        student_grade = session.query(StudentGrade).filter(
            StudentGrade.Name == grade
        ).first()
        if student_grade is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The provided student grade is invalid or could not be found!")

        all_students = session.query(Student).filter(
            Student.StudentEnabled == 1,
            Student.GradeID == student_grade.id
        ).order_by(Student.LastName).all()
        # Iterate through each student record in the specified grade level and accumulate student care hours in seconds.
        all_student_hours = {}
        for student in all_students:
            student_care_records = session.query(StudentCareHours).filter(
                StudentCareHours.StudentID == student.StudentID,
                StudentCareHours.CareDate.between(start_date, end_date)
            ).all()
            all_student_hours[student.StudentID] = {
                "student_id": student.StudentID,
                "first_name": student.FirstName.capitalize(),
                "last_name": student.LastName.capitalize(),
                "before_care_hours": 0,
                "after_care_hours": 0
            }
            if student_care_records:
                for record in student_care_records:
                    time_taken_in_seconds = (datetime.combine(date.min, record.CheckOutTime) - datetime.combine(date.min, record.CheckInTime)).total_seconds()
                    if not record.CareType:
                        all_student_hours[student.StudentID]["before_care_hours"] += time_taken_in_seconds
                    else:
                        all_student_hours[student.StudentID]["after_care_hours"] += time_taken_in_seconds
        # The accumulated hours at this point is in seconds, and must be converted to hours and minutes for displaying/reporting.
        for student_id in all_student_hours.keys():
            time_taken_before_care_formatted = str(timedelta(seconds=int(all_student_hours[student_id]['before_care_hours'])))
            time_taken_after_care_formatted = str(timedelta(seconds=int(all_student_hours[student_id]['after_care_hours'])))
            all_student_hours[student_id]['before_care_hours'] = time_taken_before_care_formatted
            all_student_hours[student_id]['after_care_hours'] = time_taken_after_care_formatted
        session.commit()
    except IntegrityError as err:
        raise RuntimeError from err
    return all_student_hours


async def get_student_care_records(pyd_student_care: PydanticRetrieveStudentCareRecord, session: Session = None):
    """
    This method is used to retrieve all before-care and after-care service records for the specified student
    over the range of dates provided.

    :param pyd_student_care: The student ID, start date and end date of the student care records to retrieve.
    :type pyd_student_care: PydanticRetrieveStudentCareRecord, required
    :param session: The database session used to retrieve student care records.
    :type session: Session, optional
    :return: A JSON-Compatible dictionary containing the before-care and after-care service for the range of dates provided for the specified student.
    :rtype: Dict[str, any]
    :raises HTTPException: If any of the provided parameters are invalid, or the student ID does not exist.
    """
    if session is None:
        session = next(get_db_session())
    if None in (pyd_student_care.student_id, pyd_student_care.start_date, pyd_student_care.end_date):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A student ID, a care start date, and a care end date must be provided!")
    if not check_date_formats([pyd_student_care.start_date, pyd_student_care.end_date]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Either the care start date or the care end date provided was in an incorrect format! Ensure the dates are in YYYY-MM-DD format!")

    student_exists = session.query(Student).filter(Student.StudentID == pyd_student_care.student_id).first()
    if student_exists is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The provided student ID does not exist!")

    found_records = {}
    pyd_student_care.student_id = pyd_student_care.student_id.lower().strip()
    care_records = session.query(Student, StudentCareHours).filter(
        Student.StudentID == pyd_student_care.student_id,
        StudentCareHours.StudentID == pyd_student_care.student_id,
        StudentCareHours.CareDate.between(pyd_student_care.start_date, pyd_student_care.end_date)
    ).order_by(desc(StudentCareHours.CareDate)).all()
    for record in care_records:
        if found_records.get(record[1].CareDate, None) is None:
            found_records[record[1].CareDate] = {
                "student": record[0].as_limited_dict(),
            }
        if not record[1].CareType:
            found_records[record[1].CareDate].update({
                "before_care": record[1].as_dict(),
            })
        elif record[1].CareType:
            found_records[record[1].CareDate].update({
                "after_care": record[1].as_dict(),
            })
    session.commit()
    return found_records


async def get_care_students_by_grade(pyd_care_students: PydanticRetrieveCareStudentsByGrade, session: Session = None) -> List[Dict[str, any]]:
    """
    This method is used to retrieve all the students in a specific grade level that has care records for
    the provided date and care service type. The student and student care records returned also include
    if the student is applicable to be checked-in to the specified care type.

    :param pyd_care_students: The student grade level, care type, and care date.
    :type pyd_care_students: PydanticRetrieveCareStudentsByGrade, required
    :param session: The database session used to retrieve students with care records by grade level and care date.
    :type session: Session, optional
    :return: A list of students in the specified grade level that has had participated in the specified care type on the specified care date.
    :rtype: List[Dict[str, any]]
    """
    if session is None:
        session = next(get_db_session())
    if None in (pyd_care_students.student_grade, pyd_care_students.care_date, pyd_care_students.care_type):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A student grade, a care type, and a care date must be provided!")
    if not check_date_formats(pyd_care_students.care_date):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Either the care start date or the care end date provided was in an incorrect format! Ensure the dates are in YYYY-MM-DD format!")

    pyd_care_students.student_grade = pyd_care_students.student_grade.lower().strip()
    pyd_care_students.care_date = pyd_care_students.care_date.strip()
    student_list = []
    all_students_in_grade = session.query(Student, StudentGrade).filter(
        Student.GradeID == StudentGrade.id,
        StudentGrade.Name == pyd_care_students.student_grade,
    ).order_by(asc(Student.StudentID)).all()
    for student in all_students_in_grade:
        student_checked_in = session.query(StudentCareHours).filter(
            StudentCareHours.StudentID == student[0].StudentID,
            StudentCareHours.CareDate == pyd_care_students.care_date,
            StudentCareHours.CareType == pyd_care_students.care_type
        ).first()
        student_dict = {
            "student": student[0].as_dict(),
        }
        if student_checked_in:
            student_dict["not_applicable"] = True
        else:
            student_dict["not_applicable"] = False
        student_list.append(student_dict)
    return student_list


async def check_in_student(pyd_student_checkin: PydanticStudentCareHoursCheckIn, session: Session = None):
    """
    This method is used to check in a student into either before-care or after-care services for the specified date.
    The current time and check-in signature is provided when the record is created and the check-out time is
    automatically set to the maximum length of the timeslot unless the student has been manually checked out.
    An email is automatically sent to the primary and secondary emails associated with the student's account
    notifying parents that their child has been checked-in of care services. This email is only
    sent to the parent email if notifications are enabled.

    :param pyd_student_checkin: The student ID, care date, care type, check-in time, and check-in signature.
    :type pyd_student_checkin: PydanticStudentCareHoursCheckIn, required
    :param session: The database session used to add a student care record to the database.
    :type session: Session, optional
    :return: None
    :rtype: None
    :raises HTTPException: If any of the provided parameters are invalid, the current time is not within the timeslot time of the care service, or the student is already checked out.
    """
    if session is None:
        session = next(get_db_session())

    pyd_student_checkin.student_id = pyd_student_checkin.student_id.lower().strip()
    pyd_student_checkin.check_in_signature = pyd_student_checkin.check_in_signature.lower().strip()
    student_care = session.query(StudentCareHours).filter(
        StudentCareHours.StudentID == pyd_student_checkin.student_id,
        StudentCareHours.CareDate == pyd_student_checkin.check_in_date,
        StudentCareHours.CareType == pyd_student_checkin.care_type
    ).first()
    if student_care is None:
        try:
            check_in_time = datetime.strptime(time.strftime('%H:%M'), '%H:%M') if pyd_student_checkin.check_in_time is None else datetime.strptime(pyd_student_checkin.check_in_time, '%H:%M')
            check_out_time = datetime.strptime(ConfigManager().config()['Student Care Settings']['before_care_check_out_time'] if not pyd_student_checkin.care_type else ConfigManager().config()['Student Care Settings']['after_care_check_out_time'], '%H:%M')
            if not pyd_student_checkin.care_type:
                if (check_in_time - datetime.strptime(ConfigManager().config()['Student Care Settings']['before_care_check_in_time'], '%H:%M')).total_seconds() < 0:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                        detail=f"The student cannot be checked in to before-care at {check_in_time.time()} before the service starts at {ConfigManager().config()['Student Care Settings']['before_care_check_in_time']}!")
            else:
                if (check_in_time - datetime.strptime(ConfigManager().config()['Student Care Settings']['after_care_check_in_time'], '%H:%M')).total_seconds() < 0:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                        detail=f"The student cannot be checked in to after-care at {check_in_time.time()} before the service starts at {ConfigManager().config()['Student Care Settings']['after_care_check_in_time']}!")

            if (check_out_time - check_in_time).total_seconds() <= 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=f"The student cannot be checked in after the end of the student care service!")
            new_student_care_hours = StudentCareHours(
                pyd_student_checkin.student_id,
                pyd_student_checkin.check_in_date,
                pyd_student_checkin.care_type,
                check_in_time,
                check_out_time,
                pyd_student_checkin.check_in_signature
            )
            session.add(new_student_care_hours)
            session.commit()
            LoggingManager().log(LoggingManager.LogLevel.LOG_INFO,
                                 f"A student: {pyd_student_checkin.student_id} has been checked-in to {'after-care' if pyd_student_checkin.care_type else 'before-care'} services on {pyd_student_checkin.check_in_date} at {check_in_time}.",
                                 origin=LOG_ORIGIN_API, no_print=False)
        except IntegrityError as err:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    else:
        if student_care.ManuallyCheckedOut:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"The student has already checked out from {'after' if student_care.CareType else 'before'}-care for the day!")
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"This student has already checked-in for {'after' if student_care.CareType else 'before'}-care at {student_care.CheckInTime} "
                                       f"for the provided date: {pyd_student_checkin.check_in_date}")
    # Send notification to enabled emails that the student has been checked-in.
    student_record = session.query(Student).filter(Student.StudentID == pyd_student_checkin.student_id).first()
    care_type_text = "Before-Care Services" if not pyd_student_checkin.care_type else "After-Care Services"
    if student_record:
        if student_record.StudentContactInfo.EnablePrimaryEmailNotifications:
            send_email(
                to_user=f'{student_record.StudentContactInfo.ParentOneFirstName} {student_record.StudentContactInfo.ParentOneLastName}',
                to_email=[student_record.StudentContactInfo.PrimaryEmail],
                subj=f"Student Checked In To {care_type_text}",
                messages=[
                    f"<b>{student_record.FirstName.capitalize()} {student_record.LastName.capitalize()}</b> has been checked in to {care_type_text} by {pyd_student_checkin.check_in_signature}.",
                    f"If you're not aware of your student being checked in to {care_type_text} today, then please contact administration."
                ],
            )
        if student_record.StudentContactInfo.EnableSecondaryEmailNotifications:
            send_email(
                to_user=f'{student_record.StudentContactInfo.ParentTwoFirstName} {student_record.StudentContactInfo.ParentTwoLastName}',
                to_email=[student_record.StudentContactInfo.SecondaryEmail],
                subj=f"Student Checked In To {care_type_text}",
                messages=[
                    f"<b>{student_record.FirstName.capitalize()} {student_record.LastName.capitalize()}</b> has been checked in to {care_type_text} by {pyd_student_checkin.check_in_signature}.",
                    f"If you're not aware of your student being checked in to {care_type_text} today, then please contact administration."
                ],
            )
    return new_student_care_hours


async def check_out_student(pyd_student_checkout: PydanticStudentCareHoursCheckOut, session: Session = None):
    """
    This method is used to check out a student from either before-care or after-care services for the specified date.
    The current time and check-out signature is provided when the record is updated. The check-out time is
    set to the current time when the student is checked out.
    An email is automatically sent to the primary and secondary emails associated with the student's account
    notifying parents that their child has been checked-out of care services. This email is only
    sent to the parent email if notifications are enabled.

    :param pyd_student_checkout: The student ID, care date, care type, check-out time, and check-out signature.
    :type pyd_student_checkout: PydanticStudentCareHoursCheckOut, required
    :param session: The database session used to add a student care record to the database.
    :type session: Session, optional
    :return: None
    :rtype: None
    :raises HTTPException: If any of the provided parameters are invalid, the current time is not within the timeslot time of the care service, or the student is already checked out.
    """
    if session is None:
        session = next(get_db_session())

    pyd_student_checkout.student_id = pyd_student_checkout.student_id.lower().strip()
    pyd_student_checkout.check_out_signature = pyd_student_checkout.check_out_signature.lower().strip()
    student_care = session.query(StudentCareHours).filter(
        StudentCareHours.StudentID == pyd_student_checkout.student_id,
        StudentCareHours.CareDate == pyd_student_checkout.check_out_date,
        StudentCareHours.CareType == pyd_student_checkout.care_type
    ).first()
    if student_care is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The student is not checked in to the current service, so the student cannot be checked out!")
    if student_care.ManuallyCheckedOut:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"The student has already checked out from {'after' if student_care.CareType else 'before'}-care for the day!")
    try:
        if not pyd_student_checkout.care_type:
            check_out_time = datetime.strptime(ConfigManager().config()['Student Care Settings']['before_care_check_out_time'], '%H:%M') if pyd_student_checkout.check_out_time is None else datetime.strptime(pyd_student_checkout.check_out_time, '%H:%M')
            if (check_out_time - datetime.strptime(ConfigManager().config()['Student Care Settings']['before_care_check_out_time'], '%H:%M')).total_seconds() > 0:
                check_out_time = datetime.strptime(ConfigManager().config()['Student Care Settings']['before_care_check_out_time'], '%H:%M')
            if (check_out_time - datetime.strptime(student_care.CheckInTime.strftime("%H:%M"), '%H:%M')).total_seconds() < 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=f"The provided check-out time of {check_out_time.time()} is invalid! Please ensure the check-out time is after the student's check-in time of: {student_care.CheckInTime}")
        else:
            check_out_time = datetime.strptime(ConfigManager().config()['Student Care Settings']['after_care_check_out_time'], '%H:%M') if pyd_student_checkout.check_out_time is None else datetime.strptime(pyd_student_checkout.check_out_time, '%H:%M')
            if (check_out_time - datetime.strptime(ConfigManager().config()['Student Care Settings']['after_care_check_out_time'], '%H:%M')).total_seconds() > 0:
                check_out_time = datetime.strptime(ConfigManager().config()['Student Care Settings']['after_care_check_out_time'], '%H:%M')
            if (check_out_time - datetime.strptime(student_care.CheckInTime.strftime("%H:%M"), '%H:%M')).total_seconds() < 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=f"The provided check-out time of {check_out_time.time()} is invalid! Please ensure the check-out time is after the student's check-in time of: {student_care.CheckInTime}")

        student_care.CheckOutTime = check_out_time
        student_care.CheckOutSignature = pyd_student_checkout.check_out_signature
        student_care.ManuallyCheckedOut = True
        session.commit()
        LoggingManager().log(LoggingManager.LogLevel.LOG_INFO,
                             f"A student: {pyd_student_checkout.student_id} has been manually checked-out of "
                             f"{'after-care' if pyd_student_checkout.care_type else 'before-care'} services on {pyd_student_checkout.check_out_date} at "
                             f"{student_care.CheckOutTime}.",
                             origin=LOG_ORIGIN_API, no_print=False)
    except IntegrityError as err:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    # Send notification to enabled emails that the student has been checked-in.
    student_record = session.query(Student).filter(Student.StudentID == pyd_student_checkout.student_id).first()
    care_type_text = "Before-Care Services" if not pyd_student_checkout.care_type else "After-Care Services"
    if student_record:
        if student_record.StudentContactInfo.EnablePrimaryEmailNotifications:
            send_email(
                to_user=f'{student_record.StudentContactInfo.ParentOneFirstName} {student_record.StudentContactInfo.ParentOneLastName}',
                to_email=[student_record.StudentContactInfo.PrimaryEmail],
                subj=f"Student Checked Out Of {care_type_text}",
                messages=[
                    f"<b>{student_record.FirstName.capitalize()} {student_record.LastName.capitalize()}</b> has been checked out of {care_type_text} by {student_care.CheckOutSignature}.",
                    f"If you're not aware of your student being checked out of {care_type_text} today, then please contact administration."
                ],
            )
        if student_record.StudentContactInfo.EnableSecondaryEmailNotifications:
            send_email(
                to_user=f'{student_record.StudentContactInfo.ParentTwoFirstName} {student_record.StudentContactInfo.ParentTwoLastName}',
                to_email=[student_record.StudentContactInfo.SecondaryEmail],
                subj=f"Student Checked Out Of {care_type_text}",
                messages=[
                    f"<b>{student_record.FirstName.capitalize()} {student_record.LastName.capitalize()}</b> has been checked out of {care_type_text} by {student_care.CheckOutSignature}.",
                    f"If you're not aware of your student being checked out of {care_type_text} today, then please contact administration."
                ],
            )
    return student_care
