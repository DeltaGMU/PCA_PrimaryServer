"""
Requires GTK-3 Runtime Libraries!
"""

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
from sqlalchemy.orm import Session
from server.lib.utils.date_utils import check_date_formats
from server.lib.strings import ROOT_DIR
from server.lib.database_manager import get_db_session
from server.lib.database_access.analytics_interface import check_time_sheets_submitted, get_all_time_sheets_for_report

env = Environment(loader=FileSystemLoader(
    [
        f'{ROOT_DIR}/lib/report_generation'
    ]
))


async def create_time_sheets_report(start_date: str, end_date: str, session: Session = None):
    if session is None:
        session = next(get_db_session())
    if not check_date_formats([start_date, end_date]):
        raise RuntimeError("The start and end dates for the reporting period are invalid!")
    template = env.get_template(f'timesheet_report_template.html')
    template_vars = {
        "title": "Employee Timesheet Report",
        "pca_logo": f"{ROOT_DIR}\\lib\\report_generation\\pca_logo.svg",
        "time_sheet_list": []
    }
    all_employees, fully_submitted_count, not_submitted_count = await check_time_sheets_submitted(session)
    all_employee_hours = await get_all_time_sheets_for_report(session)
    time_sheet_list = []
    for employee_id in all_employee_hours.keys():
        for employee in all_employees:
            if employee.EmployeeID == employee_id:
                employee_name = f"{employee.FirstName} {employee.LastName}"
                time_sheet_list.append(
                    [
                        employee_id,
                        employee_name,
                        all_employee_hours[employee_id]['work_hours'],
                        all_employee_hours[employee_id]['pto_hours'],
                        all_employee_hours[employee_id]['extra_hours']
                    ]
                )
    template_vars["time_sheet_list"] = time_sheet_list
    reformat_date = f"{start_date[0:4]}_{start_date[5:7]}"
    generated_pdf_path = f"{ROOT_DIR}/reports/{reformat_date}-EmployeeReport.pdf"
    html_out = template.render(template_vars)
    HTML(string=html_out, base_url=f".").write_pdf(
        generated_pdf_path,
        stylesheets=[
            CSS(f"{ROOT_DIR}/lib/report_generation/styles.css"),
            CSS(f"{ROOT_DIR}/lib/report_generation/bootstrap.min.css")
        ]
    )
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
    HTML(string=html_out, base_url=f".").write_pdf("StudentCareReport.pdf", stylesheets=["styles.css", CSS("bootstrap.min.css")])
