import time
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from server.lib.data_classes.student_grade import StudentGrade
from server.lib.config_manager import ConfigManager
from server.lib.data_classes.student import Student
from server.lib.utils.date_utils import check_date_formats
from server.lib.data_classes.student_care_hours import StudentCareHours, PydanticStudentCareHoursCheckOut, PydanticRetrieveCareStudentsByGrade
from server.lib.data_classes.student_care_hours import PydanticStudentCareHoursCheckIn
from server.lib.database_manager import get_db_session


async def get_one_student_care(student_id: str, care_date: str, session: Session = None):
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
        return [care.as_dict() for care in student_care]


async def get_care_students_by_grade(pyd_care_students: PydanticRetrieveCareStudentsByGrade, session: Session = None):
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
    ).all()
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
        except IntegrityError as err:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    else:
        if student_care.ManuallyCheckedOut:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"The student has already checked out from {'after' if student_care.CareType else 'before'}-care for the day!")
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"This student has already checked-in for {'after' if student_care.CareType else 'before'}-care at {student_care.CheckInTime} "
                                       f"for the provided date: {pyd_student_checkin.check_in_date}")
    return new_student_care_hours


async def check_out_student(pyd_student_checkout: PydanticStudentCareHoursCheckOut, session: Session = None):
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
    except IntegrityError as err:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return student_care
