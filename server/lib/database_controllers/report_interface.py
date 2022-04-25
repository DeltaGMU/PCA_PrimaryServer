"""
This module contains the functions that interface with the database server
to handle the processing of report generation. Any code related to the generation of reports
that require creating, reading, updating, or deleting data from the database server
must use this interface module.
"""

from datetime import datetime, timedelta, date
from typing import Dict, List
import pdfkit
import csv
from io import StringIO
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from fastapi import HTTPException, status
from jinja2 import Environment, FileSystemLoader

from server.lib.logging_manager import LoggingManager
from server.lib.config_manager import ConfigManager
from server.lib.utils.email_utils import send_email
from server.lib.data_models.report import PydanticLeaveRequest
from server.lib.utils.date_utils import check_date_formats
from server.lib.data_models.student import Student
from server.lib.data_models.student_care_hours import StudentCareHours
from server.lib.data_models.student_grade import StudentGrade
from server.lib.data_models.employee_role import EmployeeRole
from server.lib.data_models.employee import Employee
from server.lib.data_models.employee_hours import EmployeeHours
from server.lib.database_manager import get_db_session
from server.lib.strings import ROOT_DIR, LOG_ORIGIN_API

# Initializes the file system loader environment for the report generation library.
env = Environment(loader=FileSystemLoader(
    [
        f'{ROOT_DIR}/lib/report_generation'
    ]
))


async def get_all_time_sheets_for_report(start_date: str, end_date: str, session: Session = None) -> Dict[str, any]:
    """
    This method retrieves all the timesheet records for all employees over the provided range of work dates,
    and returns them as a JSON-Compatible dictionary organized by the employee ID as keys and the accumulated timesheet hours as values.
    This method returns both the total accumulated hours for each employee and the individual timesheet submission comments.
    This method is utilized by the report generation system to generate employee timesheet PDF reports.

    :param start_date: The start work date for the range of employee timesheet records to retrieve.
    :type start_date: str, required
    :param end_date: The end work date for the range of employee timesheet records to retrieve.
    :type end_date: str, required
    :param session: The database session that is used to retrieve all employee timesheet records over the provided range of work dates.
    :type session: Session, optional
    :return: A JSON-Compatible dictionary containing employee IDs as keys and accumulated timesheet hours and submission comments as values.
    :rtype: Dict[str, any]
    :raises HTTPException: If an error is encountered retrieving an employee's timesheet record.
    """
    if session is None:
        session = next(get_db_session())
    try:
        # Retrieve all the employees that submitted time sheets during the provided reporting period,
        # however, ignore the default admin account if it is included and ignore timesheet records with 0-hour entries.
        # In addition, order the employee timesheet records by the employee last name.
        employee_time_sheet_records = session.query(Employee, EmployeeHours, EmployeeRole).filter(
            Employee.EmployeeEnabled == 1,
            Employee.EmployeeID != 'admin',
            EmployeeRole.id == Employee.EmployeeRoleID,
            EmployeeHours.EmployeeID == Employee.EmployeeID,
            EmployeeHours.DateWorked.between(start_date, end_date),
            or_(EmployeeHours.WorkHours > 0, EmployeeHours.PTOHours > 0, EmployeeHours.ExtraHours > 0)
        ).order_by(Employee.LastName).all()
        if employee_time_sheet_records is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Encountered an error retrieving employee time sheets!")

        # Define the data dictionary that will be used to hold the timesheet hours and comments for each employee that submitted time sheets
        # over the reporting period.
        all_employees_hours = {}
        for record in employee_time_sheet_records:
            all_employees_hours[record[0].EmployeeID] = {
                "full_name": f"{record[0].FirstName.capitalize()} {record[0].LastName.capitalize()}",
                "work_hours": 0,
                "pto_hours": 0,
                "extra_hours": 0,
                "comments": []
            }

        # For each employee timesheet record, accumulate the total work hours, pto hours, and extra hours for each employee.
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


async def get_all_time_sheets_for_csv(start_date: str, end_date: str, session: Session = None) -> List[List[str]]:
    """
    This method retrieves all the timesheet records for all employees over the provided range of work dates,
    and returns them as a JSON-Compatible dictionary organized by the employee ID as keys and the individual timesheet records as values.
    This method is utilized by the report generation system to generate employee timesheet CSV spreadsheets.

    :param start_date: The start work date for the range of employee timesheet records to retrieve.
    :type start_date: str, required
    :param end_date: The end work date for the range of employee timesheet records to retrieve.
    :type end_date: str, required
    :param session: The database session that is used to retrieve all employee timesheet records over the provided range of work dates.
    :type session: Session, optional
    :return: A list of all the employee timesheet records that were submitted over the provided range of work dates.
    :rtype: List[List[str]]
    :raises HTTPException: If an error is encountered retrieving an employee's timesheet record.
    """
    if session is None:
        session = next(get_db_session())
    try:
        # Retrieve all the employees that submitted time sheets during the provided reporting period,
        # however, ignore the default admin account if it is included and ignore timesheet records with 0-hour entries.
        # In addition, order the employee timesheet records by the employee last name.
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
        # For each retrieved employee timesheet record, format it as per the columns listed below for CSV spreadsheets.
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
    """
    This utility method retrieves all the employees that submitted time sheets during the provided range of work dates,
    and returns them as a list of employee records.

    :param start_date: The start work date for the range of employee timesheet records to query.
    :type start_date: str, required
    :param end_date: The end work date for the range of employee timesheet records to query.
    :type end_date: str, required
    :param session: The database session that is used to retrieve all employee records that had timesheet submissions during the provided range of work dates.
    :type session: Session, optional
    :return: A list of employee records that had timesheet submissions during the provided range of work dates.
    :rtype: List[Employee]
    """
    if session is None:
        session = next(get_db_session())
    all_employees = session.query(Employee, EmployeeHours).filter(
        Employee.EmployeeEnabled == 1,
        EmployeeHours.EmployeeID == Employee.EmployeeID,
        EmployeeHours.DateWorked.between(start_date, end_date)
    ).all()
    session.commit()
    return all_employees[0]


async def get_all_student_care_for_report(start_date: str, end_date: str, grade: str, session: Session = None) -> Dict[str, any]:
    """
    This method retrieves all the student care records for all students over the provided range of student care dates,
    and returns them as a JSON-Compatible dictionary organized by the student ID as keys and the accumulated student care hours as values.
    This method is utilized by the report generation system to generate student care service PDF reports.

    :param start_date: The start date for the range of student care records to retrieve.
    :type start_date: str, required
    :param end_date: The end date for the range of student care records to retrieve.
    :type end_date: str, required
    :param session: The database session that is used to retrieve all student care records over the provided range of dates.
    :type session: Session, optional
    :return: A JSON-Compatible dictionary containing student IDs as keys and accumulated student care hours as values.
    :rtype: Dict[str, any]
    :raises HTTPException: If an error is encountered retrieving a student's care service record.
    """
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
        ).order_by(Student.LastName).all()
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


async def get_all_student_care_for_csv(start_date: str, end_date: str, grade: str, session: Session = None) -> List[List[str]]:
    """
    This method retrieves all the student care records for all students over the provided range of student care dates,
    and returns them as a JSON-Compatible dictionary organized by the student ID as keys and a list of individual service records as values.
    This method is utilized by the report generation system to generate student care service CSV spreadsheets.

    :param start_date: The start date for the range of student care records to retrieve.
    :type start_date: str, required
    :param end_date: The end date for the range of student care records to retrieve.
    :type end_date: str, required
    :param session: The database session that is used to retrieve all student care records over the provided range of dates.
    :type session: Session, optional
    :return: A list of student care service records retrieved from the provided range of dates.
    :rtype: List[List[str]]
    :raises HTTPException: If an error is encountered retrieving a student's care service record.
    """
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
        ).order_by(Student.LastName).all()
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


async def create_time_sheets_csv(start_date: str, end_date: str, session: Session = None) -> str:
    """
    This method is used to generate a CSV spreadsheet containing all the employee timesheet records
    that were submitted over the provided range of work dates.

    :param start_date: The start work date for the range of employee timesheet records to retrieve.
    :type start_date: str, required
    :param end_date: The end work date for the range of employee timesheet records to retrieve.
    :type end_date: str, required
    :param session: The database session that is used to retrieve all employee timesheet records over the provided range of work dates.
    :type session: Session, optional
    :return: Returns a comma-separated string containing all the CSV rows of employee timesheet records over the provided range of work dates.
    :rtype: str
    """
    if session is None:
        session = next(get_db_session())
    if not check_date_formats([start_date, end_date]):
        raise RuntimeError("The start and end dates for the reporting period are invalid!")
    employee_hours_list = await get_all_time_sheets_for_csv(start_date, end_date, session)
    mem_file = StringIO()
    csv.writer(mem_file).writerows(employee_hours_list)
    LoggingManager().log(LoggingManager.LogLevel.LOG_INFO,
                         f"A timesheet CSV spreadsheet was generated for the reporting period: {start_date} - {end_date}.",
                         origin=LOG_ORIGIN_API, no_print=False)
    return mem_file.getvalue()


async def create_student_care_csv(start_date: str, end_date: str, grade: str, session: Session = None):
    """
    This method is used to generate a CSV spreadsheet containing all the student care service records
    from students of the provided grade level that were created over the provided range of dates.

    :param start_date: The start date for the range of student care records to retrieve.
    :type start_date: str, required
    :param end_date: The end date for the range of student care records to retrieve.
    :type end_date: str, required
    :param grade: The student grade level for which to retrieve student records from.
    :type grade: str, required
    :param session: The database session that is used to retrieve all student care records over the provided range of dates.
    :type session: Session, optional
    :return: Returns a comma-separated string containing all the CSV rows of student care records over the provided range of dates.
    :rtype: str
    """
    if session is None:
        session = next(get_db_session())
    if not check_date_formats([start_date, end_date]):
        raise RuntimeError("The start and end dates for the reporting period are invalid!")
    if grade is None:
        raise RuntimeError("Creating a student care csv report requires a grade to be provided!")
    employee_hours_list = await get_all_student_care_for_csv(start_date.strip(), end_date.strip(), grade.strip(), session)
    mem_file = StringIO()
    csv.writer(mem_file).writerows(employee_hours_list)
    LoggingManager().log(LoggingManager.LogLevel.LOG_INFO,
                         f"A student care service CSV spreadsheet was generated for the reporting period: {start_date} - {end_date}.",
                         origin=LOG_ORIGIN_API, no_print=False)
    return mem_file.getvalue()


async def create_time_sheets_report(start_date: str, end_date: str, session: Session = None) -> bytes:
    """
    This method is used to generate a PDF report containing all the employee timesheet records
    that were submitted over the provided range of work dates.

    :param start_date: The start work date for the range of employee timesheet records to retrieve.
    :type start_date: str, required
    :param end_date: The end work date for the range of employee timesheet records to retrieve.
    :type end_date: str, required
    :param session: The database session that is used to retrieve all employee timesheet records over the provided range of work dates.
    :type session: Session, optional
    :return: Returns a byte-string containing all the employee timesheet records over the provided range of work dates.
    :rtype: bytes
    """
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
    LoggingManager().log(LoggingManager.LogLevel.LOG_INFO,
                         f"A timesheet PDF report was generated for the reporting period: {start_date} - {end_date}.",
                         origin=LOG_ORIGIN_API, no_print=False)
    return pdf_bytes


async def create_student_care_report(start_date, end_date, grade, session) -> bytes:
    """
    This method is used to generate a PDF report containing all the student care service records
    from students of the provided grade level that were created over the provided range of dates.

    :param start_date: The start date for the range of student care records to retrieve.
    :type start_date: str, required
    :param end_date: The end date for the range of student care records to retrieve.
    :type end_date: str, required
    :param grade: The student grade level for which to retrieve student records from.
    :type grade: str, required
    :param session: The database session that is used to retrieve all student care records over the provided range of dates.
    :type session: Session, optional
    :return: Returns a byte-string containing all the student care records over the provided range of dates.
    :rtype: bytes
    """
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
    LoggingManager().log(LoggingManager.LogLevel.LOG_INFO,
                         f"A student care service PDF report was generated for the reporting period: {start_date} - {end_date}.",
                         origin=LOG_ORIGIN_API, no_print=False)
    return pdf_bytes


async def create_leave_request_email(leave_request: PydanticLeaveRequest, session: Session = None):
    """
    This method is used to create and email the appropriate administration staff containing
    the leave request of an employee.

    :param leave_request: The information from a leave request form required to submit a leave request.
    :type leave_request: PydanticLeaveRequest
    :param session: The database session used to verify the employee ID provided in the leave request.
    :type session: Session, optional
    :return: True if the leave request was successfully formatted and emailed to the appropriate administration staff.
    :rtype: bool
    :raises HTTPException: If the provided employee ID was invalid or if an error occurred preventing the leave request email from being sent.
    """
    if session is None:
        session = next(get_db_session())
    if not check_date_formats([leave_request.date_of_absence_start, leave_request.date_of_absence_end]):
        raise RuntimeError("The start and end dates for the reporting period are invalid!")
    mailing_address = ConfigManager().config()['System Settings']['leave_request_mailing_address'].strip()
    formatted_start_date = datetime.strptime(leave_request.date_of_absence_start, "%Y-%m-%d").strftime("%m/%d/%Y")
    formatted_end_date = datetime.strptime(leave_request.date_of_absence_end, "%Y-%m-%d").strftime("%m/%d/%Y")

    matching_employee = session.query(Employee).filter(
        Employee.EmployeeID == leave_request.employee_id,
    ).first()
    if matching_employee is None:
        raise RuntimeError("The leave request could not be sent because the provided employee ID does not match any employee records!")
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
                    template="leave_request_email_template.html",
                    to_cc=matching_employee.EmployeeContactInfo.PrimaryEmail
                )
    if sent_email:
        LoggingManager().log(LoggingManager.LogLevel.LOG_INFO,
                             f"A leave request was created by: {matching_employee.EmployeeID} and has been emailed to administration",
                             origin=LOG_ORIGIN_API, no_print=False)
        return True
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The email could not be sent!")


async def get_leave_request_reasons() -> List[str]:
    """
    This utility method retrieves the comma-separated list of reasons for an employee leave request
    from the server configuration file and formats it into a python list.

    :return: A list of all the leave-request reasons from the server configuration file.
    :rtype: List[str]
    """
    leave_request_strings = ConfigManager().config()['System Settings']['leave_request_reasons']
    leave_request_list = [reason.strip() for reason in leave_request_strings.split(",")]
    return leave_request_list
