import time
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from config import ENV_SETTINGS
from server.lib.data_classes.student_care_hours import StudentCareHours, PydanticStudentCareHoursCheckOut
from server.lib.data_classes.student_care_hours import PydanticStudentCareHoursCheckIn
from server.lib.database_manager import get_db_session


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
            check_out_time = datetime.strptime(ENV_SETTINGS.student_before_care_check_out_time if not pyd_student_checkin.care_type else ENV_SETTINGS.student_after_care_check_out_time, '%H:%M')
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"This student has already checked-in for {'after' if student_care.CareType else 'before'}-care "
                                   f"for the provided date: {pyd_student_checkin.check_in_date}")
    return new_student_care_hours


async def check_out_student(pyd_student_checkout: PydanticStudentCareHoursCheckOut, session: Session = None):
    # Not Implemented!
    return {}
