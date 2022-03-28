from datetime import datetime
from fastapi import HTTPException, status
import pdfkit
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from jinja2 import Environment, FileSystemLoader
from server.lib.strings import ROOT_DIR
from server.lib.database_access.report_interface import get_all_time_sheets_for_report, get_all_student_care_for_report
from server.lib.utils.date_utils import check_date_formats
from server.lib.utils.reports_utils import delete_time_sheet_report, delete_care_report
from server.lib.data_classes.student_grade import StudentGrade, PydanticStudentGrade
from server.lib.database_manager import get_db_session

env = Environment(loader=FileSystemLoader(
    [
        f'{ROOT_DIR}/lib/report_generation'
    ]
))


async def retrieve_all_grades(session: Session = None):
    if session is None:
        session = next(get_db_session())
    all_grades = session.query(StudentGrade).all()
    return all_grades


async def retrieve_one_grade(grade_name: str, session: Session = None):
    if grade_name is None or len(grade_name) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The provided student grade is invalid or empty!")
    if session is None:
        session = next(get_db_session())
    grade_name = grade_name.lower().strip()
    matching_grade = session.query(StudentGrade).filter(
        StudentGrade.Name == grade_name
    ).first()
    if matching_grade is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The student grade information for the student could not be created due to invalid parameters!")
    return matching_grade


async def create_student_grade(student_grade: PydanticStudentGrade, session: Session = None):
    student_grade = student_grade.student_grade
    if len(student_grade) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The student grade name cannot be empty!")
    if session is None:
        session = next(get_db_session())
    student_grade = student_grade.lower().strip()
    grade_exists = session.query(StudentGrade).filter(StudentGrade.Name == student_grade).first()
    if grade_exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"The student grade: '{student_grade}' already exists!")
    try:
        new_student_grade = StudentGrade(student_grade)
        session.add(new_student_grade)
        session.commit()
    except IntegrityError as err:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return new_student_grade


async def remove_student_grade(student_grade: PydanticStudentGrade, session: Session = None):
    student_grade = student_grade.student_grade.lower().strip()
    if len(student_grade) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The student grade name cannot be empty!")
    if session is None:
        session = next(get_db_session())
    try:
        matching_grade = session.query(StudentGrade).filter(StudentGrade.Name == student_grade).first()
        if matching_grade is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The provided student grade does not exist!")
        session.delete(matching_grade)
        session.commit()
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove a student grade that is currently in use!")
    except SQLAlchemyError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return matching_grade


async def delete_time_sheet_report_by_file_name(file_name: str):
    if delete_time_sheet_report(file_name):
        return file_name
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='The provided file name was invalid! Please ensure it is in the "YYYY-MM_YYYY-MM_EmployeeReport" format!')


async def delete_care_report_by_file_name(file_name: str):
    if delete_care_report(file_name):
        return file_name
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='The provided file name was invalid! Please ensure it is in the "YYYY-MM_YYYY-MM_StudentReport" format!')


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
    reformat_date = f"{start_date[0:4]}_{start_date[5:7]}"
    generated_pdf_path = f"{ROOT_DIR}/reports/employees/{reformat_date}-EmployeeReport.pdf"
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
    pdfkit.from_string(html_out,
                       generated_pdf_path,
                       css=[
                           f"{ROOT_DIR}/lib/report_generation/styles.css"
                       ],
                       options=options)
    return generated_pdf_path


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

    reformat_date = f"{start_date[0:4]}_{start_date[5:7]}"
    generated_pdf_path = f"{ROOT_DIR}/reports/students/{reformat_date}-StudentReport.pdf"
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
    pdfkit.from_string(html_out,
                       generated_pdf_path,
                       css=[
                           f"{ROOT_DIR}/lib/report_generation/styles.css"
                       ],
                       options=options)
    return generated_pdf_path
