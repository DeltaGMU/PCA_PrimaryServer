from datetime import datetime, timedelta, date
import pdfkit
import csv
from io import StringIO
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from fastapi import HTTPException, status
from jinja2 import Environment, FileSystemLoader

from server.lib.config_manager import ConfigManager
from server.lib.utils.email_utils import send_email
from server.lib.data_classes.report import PydanticLeaveRequest
from server.lib.utils.date_utils import check_date_formats
from server.lib.data_classes.student import Student
from server.lib.data_classes.student_care_hours import StudentCareHours
from server.lib.data_classes.student_grade import StudentGrade
from server.lib.data_classes.employee_role import EmployeeRole
from server.lib.data_classes.employee import Employee
from server.lib.data_classes.employee_hours import EmployeeHours
from server.lib.database_manager import get_db_session
from server.lib.strings import ROOT_DIR

env = Environment(loader=FileSystemLoader(
    [
        f'{ROOT_DIR}/lib/report_generation'
    ]
))


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


async def get_all_time_sheets_for_csv(start_date: str, end_date: str, session: Session = None):
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
        ).order_by(EmployeeHours.DateWorked).all()
        if employee_time_sheet_records is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Encountered an error retrieving employee time sheets!")
        employee_hours_list = [['date', 'employee_id', 'first_name', 'last_name', 'work_hours', 'pto_hours', 'extra_hours', 'comments']]
        for item in employee_time_sheet_records:
            employee_hours_list.append([
                item[1].DateWorked,
                item[0].EmployeeID,
                item[0].FirstName,
                item[0].LastName,
                item[1].WorkHours,
                item[1].PTOHours,
                item[1].ExtraHours,
                item[1].Comment
            ])
    except IntegrityError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return employee_hours_list


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


async def get_all_student_care_for_csv(start_date: str, end_date: str, grade: str, session: Session = None):
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

        student_hours_list = [['date', 'student_id', 'first_name', 'last_name', 'before_care_hours',
                               'before_care_check_in_signature', 'before_care_check_out_signature',
                               'after_care_hours', 'after_care_check_in_signature', 'after_care_check_out_signature']]
        all_student_hours = {}
        for record in student_care_records:
            all_student_hours[record[0].StudentID] = {
                "care_date": record[1].CareDate,
                "first_name": record[0].FirstName,
                "last_name": record[0].LastName,
                "before_care_hours": 0,
                "before_care_check_in_signature": "",
                "before_care_check_out_signature": "",
                "after_care_hours": 0,
                "after_care_check_in_signature": "",
                "after_care_check_out_signature": "",
            }
        for record in student_care_records:
            time_taken_in_seconds = (datetime.combine(date.min, record[1].CheckOutTime) - datetime.combine(date.min, record[1].CheckInTime)).total_seconds()
            if not record[1].CareType:
                all_student_hours[record[0].StudentID]["before_care_hours"] = str(timedelta(seconds=int(time_taken_in_seconds)))
                all_student_hours[record[0].StudentID]["before_care_check_in_signature"] = record[1].CheckInSignature
                all_student_hours[record[0].StudentID]["before_care_check_out_signature"] = "Automated Check-Out" if record[1].CheckOutSignature is None else record[1].CheckOutSignature
            else:
                all_student_hours[record[0].StudentID]["after_care_hours"] = str(timedelta(seconds=int(time_taken_in_seconds)))
                all_student_hours[record[0].StudentID]["after_care_check_in_signature"] = record[1].CheckInSignature
                all_student_hours[record[0].StudentID]["after_care_check_out_signature"] = "Automated Check-Out" if record[1].CheckOutSignature is None else record[1].CheckOutSignature

        for record in all_student_hours.keys():
            student = all_student_hours[record]
            print(student)
            student_hours_list.append([
                student["care_date"],
                record,
                student["first_name"],
                student["last_name"],
                student["before_care_hours"],
                student["before_care_check_in_signature"],
                student["before_care_check_out_signature"],
                student["after_care_hours"],
                student["after_care_check_in_signature"],
                student["after_care_check_out_signature"]
            ])
        session.commit()
    except IntegrityError as err:
        raise RuntimeError from err
    return student_hours_list


async def create_time_sheets_csv(start_date: str, end_date: str, session: Session = None):
    if session is None:
        session = next(get_db_session())
    if not check_date_formats([start_date, end_date]):
        raise RuntimeError("The start and end dates for the reporting period are invalid!")
    employee_hours_list = await get_all_time_sheets_for_csv(start_date, end_date, session)
    mem_file = StringIO()
    csv.writer(mem_file).writerows(employee_hours_list)
    print(mem_file.getvalue())
    return mem_file.getvalue()


async def create_student_care_csv(start_date: str, end_date: str, grade: str, session: Session = None):
    if session is None:
        session = next(get_db_session())
    if not check_date_formats([start_date, end_date]):
        raise RuntimeError("The start and end dates for the reporting period are invalid!")
    if grade is None:
        raise RuntimeError("Creating a student care csv report requires a grade to be provided!")
    employee_hours_list = await get_all_student_care_for_csv(start_date.strip(), end_date.strip(), grade.strip(), session)
    mem_file = StringIO()
    csv.writer(mem_file).writerows(employee_hours_list)
    print(mem_file.getvalue())
    return mem_file.getvalue()


async def create_time_sheets_report(start_date: str, end_date: str, session: Session = None):
    if session is None:
        session = next(get_db_session())
    if not check_date_formats([start_date, end_date]):
        raise RuntimeError("The start and end dates for the reporting period are invalid!")
    date_time_start_repr = datetime.strptime(start_date, '%Y-%m-%d')
    date_time_end_repr = datetime.strptime(end_date, '%Y-%m-%d')

    template = env.get_template(f'timesheet_report_template.html')
    template_vars = {
        "title": f"Employee Timesheet Report - [{datetime.strftime(date_time_start_repr, '%m/%d/%Y')} - {datetime.strftime(date_time_end_repr, '%m/%d/%Y')}]",
        "reporting_period_start": datetime.strftime(date_time_start_repr, '%m/%d/%Y'),
        "reporting_period_end": datetime.strftime(date_time_end_repr, '%m/%d/%Y'),
        "reporting_period_text": f"{date_time_start_repr.strftime('%B')} {date_time_start_repr.year}",
        "footer_text": f"This document was automatically generated by the reporting module of the PCA Timesheet and Student Care server.<br>"
                       f"<b>Providence Christian Academy - {date_time_start_repr.year}</b>",
        "time_sheet_list": []
    }
    all_employee_hours = await get_all_time_sheets_for_report(start_date, end_date, session)
    time_sheet_list = []
    for employee_id in all_employee_hours.keys():
        time_sheet_list.append(
            [
                employee_id,
                all_employee_hours[employee_id]['full_name'],
                all_employee_hours[employee_id]['work_hours'],
                all_employee_hours[employee_id]['pto_hours'],
                all_employee_hours[employee_id]['extra_hours'],
                all_employee_hours[employee_id]['comments']
            ]
        )
    template_vars["time_sheet_list"] = time_sheet_list
    html_out = template.render(template_vars)
    options = {
        'page-size': 'Letter',
        'margin-top': '0.5in',
        'margin-right': '0.5in',
        'margin-bottom': '0.5in',
        'margin-left': '0.5in',
        'dpi': 300,
        'encoding': 'UTF-8',
        'no-outline': None
    }
    pdf_bytes = pdfkit.from_string(html_out,
                                   css=[
                                       f"{ROOT_DIR}/lib/report_generation/styles.css"
                                   ],
                                   options=options)
    return pdf_bytes


async def create_student_care_report(start_date, end_date, grade, session):
    if session is None:
        session = next(get_db_session())
    if not check_date_formats([start_date, end_date]):
        raise RuntimeError("The start and end dates for the reporting period are invalid!")
    grade = grade.lower().strip()
    date_time_start_repr = datetime.strptime(start_date, '%Y-%m-%d')
    date_time_end_repr = datetime.strptime(end_date, '%Y-%m-%d')

    template = env.get_template('childcare_report_template.html')
    template_vars = {
        "title": f"Student Care Service Report - [{datetime.strftime(date_time_start_repr, '%m/%d/%Y')} - {datetime.strftime(date_time_end_repr, '%m/%d/%Y')}]",
        "reporting_period_start": datetime.strftime(date_time_start_repr, '%m/%d/%Y'),
        "reporting_period_end": datetime.strftime(date_time_end_repr, '%m/%d/%Y'),
        "reporting_period_text": f"{date_time_start_repr.strftime('%B')} {date_time_start_repr.year}",
        "footer_text": f"This document was automatically generated by the reporting module of the PCA Timesheet and Student Care server.<br>"
                       f"<b>Providence Christian Academy - {date_time_start_repr.year}</b>",
        "grade": grade.strip().upper(),
        "care_service_list": []
    }
    all_student_hours = await get_all_student_care_for_report(start_date, end_date, grade, session)
    time_sheet_list = []
    for student_id in all_student_hours.keys():
        time_sheet_list.append(
            [
                student_id,
                all_student_hours[student_id]['full_name'],
                all_student_hours[student_id]['before_care_hours'],
                all_student_hours[student_id]['after_care_hours']
            ]
        )
    template_vars["care_service_list"] = time_sheet_list
    html_out = template.render(template_vars)
    options = {
        'page-size': 'Letter',
        'margin-top': '0.5in',
        'margin-right': '0.5in',
        'margin-bottom': '0.5in',
        'margin-left': '0.5in',
        'dpi': 300,
        'encoding': 'UTF-8',
        'no-outline': None
    }
    pdf_bytes = pdfkit.from_string(html_out,
                                   css=[
                                       f"{ROOT_DIR}/lib/report_generation/styles.css"
                                   ],
                                   options=options)
    return pdf_bytes


async def create_leave_request_email(leave_request: PydanticLeaveRequest):
    if not check_date_formats([leave_request.date_of_absence_start, leave_request.date_of_absence_end]):
        raise RuntimeError("The start and end dates for the reporting period are invalid!")
    mailing_address = ConfigManager().config()['System Settings']['leave_request_mailing_address'].strip()
    formatted_start_date = datetime.strptime(leave_request.date_of_absence_start, "%Y-%m-%d").strftime("%m/%d/%Y")
    formatted_end_date = datetime.strptime(leave_request.date_of_absence_end, "%Y-%m-%d").strftime("%m/%d/%Y")
    print(mailing_address)
    sent_email = send_email(
                    to_user=f"Leave Request for {leave_request.employee_name}:",
                    to_email=mailing_address,
                    subj=f"New Leave Request - {leave_request.employee_name}",
                    messages=[
                        "<hr>",
                        f"<b>Employee ID:</b> {leave_request.employee_id}",
                        f"<b>Employee Name:</b> {leave_request.employee_name}",
                        "<hr>",
                        f"<b>Current Date</b>: {leave_request.current_date}",
                        f"<b>Absence From</b>: {formatted_start_date} to {formatted_end_date}",
                        f"<b># of full days</b>: {leave_request.num_full_days}",
                        f"<b># of half days</b>: {leave_request.num_half_days}",
                        f"<b># of hours</b>: {leave_request.num_hours}",
                        "<hr>",
                        f"<b>Absence Reason</b>: {', '.join(leave_request.absence_reason_list)}",
                        f"<b>Who will cover</b>: {leave_request.absence_cover_text}",
                        f"<b>Comments:</b> {leave_request.absence_comments}"
                    ],
                    template="leave_request_email_template.html"
                )
    if sent_email:
        return True
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The email could not be sent!")
