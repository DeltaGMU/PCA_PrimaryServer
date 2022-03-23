"""
Requires GTK-3 Runtime Libraries!
"""

from jinja2 import Environment, FileSystemLoader
import pdfkit
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from server.lib.utils.date_utils import check_date_formats
from server.lib.strings import ROOT_DIR
from server.lib.database_manager import get_db_session
from server.lib.database_access.analytics_interface import get_all_time_sheets_for_report
from server.lib.utils.reports_utils import delete_time_sheet_report

env = Environment(loader=FileSystemLoader(
    [
        f'{ROOT_DIR}/lib/report_generation'
    ]
))


async def delete_time_sheet_report_from_date(date: str):
    try:
        datetime.strptime(date, '%Y-%m')
    except ValueError:
        raise RuntimeError("The start and end dates for the reporting period are invalid!")
    formatted_path = f"{date[0:4]}_{date[5:7]}-EmployeeReport.pdf"
    if delete_time_sheet_report(formatted_path):
        return formatted_path
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='The provided date was invalid! Please ensure it is in the YYYY-MM format!')


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
    # all_employees = await get_employees_within_reporting_period(start_date, end_date, session)
    all_employee_hours = await get_all_time_sheets_for_report(start_date, end_date, session)
    time_sheet_list = []
    for employee_id in all_employee_hours.keys():
        print(all_employee_hours[employee_id])
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


async def create_student_care_report():
    template = env.get_template('childcare_report_template.html')
    template_vars = {
        "title": "Student Care Service Report",
        "pca_logo": "pca_logo.svg",
        "time_sheet_list": [
            ["id0", "student_name_0", 0, 0],
            ["id1", "student_name_1", 0, 0],
            ["id2", "student_name_2", 0, 0],
            ["id3", "student_name_3", 0, 0],
            ["id4", "student_name_4", 0, 0],
            ["id5", "student_name_5", 0, 0],
        ]
    }
    html_out = template.render(template_vars)
    # HTML(string=html_out, base_url=f".").write_pdf("StudentCareReport.pdf", stylesheets=["styles.css", CSS("bootstrap.min.css")])
