from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from fastapi import HTTPException, status
from server.lib.data_classes.student import Student
from server.lib.data_classes.student_care_hours import StudentCareHours
from server.lib.data_classes.student_grade import StudentGrade
from server.lib.data_classes.employee_role import EmployeeRole
from server.lib.data_classes.employee import Employee
from server.lib.data_classes.employee_hours import EmployeeHours
from server.lib.database_manager import get_db_session
from datetime import datetime, timedelta, date


async def get_all_time_sheets_for_report(start_date: str, end_date: str, session: Session = None):
    if session is None:
        session = next(get_db_session())
    try:

        employee_time_sheet_records = session.query(Employee, EmployeeHours, EmployeeRole).filter(
            Employee.EmployeeEnabled == 1,
            Employee.EmployeeID != 'admin',
            EmployeeRole.id == Employee.EmployeeRoleID,
            EmployeeHours.EmployeeID == Employee.EmployeeID,
            EmployeeHours.DateWorked.between(start_date, end_date),
            or_(EmployeeHours.WorkHours > 0, EmployeeHours.PTOHours > 0, EmployeeHours.ExtraHours > 0)
        ).order_by(Employee.FirstName).all()
        if employee_time_sheet_records is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Encountered an error retrieving employee time sheets!")

        all_employees_hours = {}
        for record in employee_time_sheet_records:
            all_employees_hours[record[0].EmployeeID] = {
                "full_name": f"{record[0].FirstName.capitalize()} {record[0].LastName.capitalize()}",
                "work_hours": 0,
                "pto_hours": 0,
                "extra_hours": 0,
                "comments": []
            }

        for record in employee_time_sheet_records:
            all_employees_hours[record[0].EmployeeID]["work_hours"] += record[1].WorkHours
            all_employees_hours[record[0].EmployeeID]["pto_hours"] += record[1].PTOHours
            all_employees_hours[record[0].EmployeeID]["extra_hours"] += record[1].ExtraHours
            if record[1].Comment and len(record[1].Comment) > 0:
                all_employees_hours[record[0].EmployeeID]["comments"].append({"date": datetime.strftime(record[1].DateWorked, '%Y-%m-%d'), "comment": record[1].Comment})

        session.commit()
    except IntegrityError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return all_employees_hours


async def get_employees_within_reporting_period(start_date: str, end_date: str, session: Session = None):
    if session is None:
        session = next(get_db_session())
    all_employees = session.query(Employee, EmployeeHours).filter(
        Employee.EmployeeEnabled == 1,
        EmployeeHours.EmployeeID == Employee.EmployeeID,
        EmployeeHours.DateWorked.between(start_date, end_date)
    ).all()
    session.commit()
    return all_employees[0]


async def get_all_student_care_for_report(start_date: str, end_date: str, grade: str, session: Session = None):
    if session is None:
        session = next(get_db_session())
    try:
        grade = grade.lower().strip()
        student_grade = session.query(StudentGrade).filter(
            StudentGrade.Name == grade
        ).first()
        if student_grade is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The provided student grade is invalid or could not be found!")

        student_care_records = session.query(Student, StudentCareHours).filter(
            Student.StudentEnabled == 1,
            StudentCareHours.StudentID == Student.StudentID,
            Student.GradeID == student_grade.id,
            StudentCareHours.CareDate.between(start_date, end_date)
        ).order_by(Student.FirstName).all()
        if student_care_records is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Encountered an error retrieving student care records!")

        all_student_hours = {}
        for record in student_care_records:
            all_student_hours[record[0].StudentID] = {
                "full_name": f"{record[0].FirstName.capitalize()} {record[0].LastName.capitalize()}",
                "before_care_hours": 0,
                "after_care_hours": 0
            }
        for record in student_care_records:
            time_taken_in_seconds = (datetime.combine(date.min, record[1].CheckOutTime) - datetime.combine(date.min, record[1].CheckInTime)).total_seconds()
            if not record[1].CareType:
                all_student_hours[record[0].StudentID]["before_care_hours"] += time_taken_in_seconds
            else:
                all_student_hours[record[0].StudentID]["after_care_hours"] += time_taken_in_seconds
        for item in all_student_hours.keys():
            time_taken_before_care_formatted = str(timedelta(seconds=int(all_student_hours[item]['before_care_hours'])))
            time_taken_after_care_formatted = str(timedelta(seconds=int(all_student_hours[item]['after_care_hours'])))
            all_student_hours[item]['before_care_hours'] = time_taken_before_care_formatted
            all_student_hours[item]['after_care_hours'] = time_taken_after_care_formatted
        session.commit()
    except IntegrityError as err:
        raise RuntimeError from err
    return all_student_hours
