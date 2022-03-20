"""
Requires GTK-3 Runtime Libraries!
"""

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS


env = Environment(loader=FileSystemLoader('.'))


def create_time_sheets_report():
    template = env.get_template('timesheet_report_template.html')
    template_vars = {
        "title": "Employee Timesheet Report",
        "pca_logo": "pcalogo.svg",
        "time_sheet_list": [
            ["id0", "employee_name_0", 0, 0, 0],
            ["id1", "employee_name_1", 0, 0, 0],
            ["id2", "employee_name_2", 0, 0, 0],
            ["id3", "employee_name_3", 0, 0, 0],
            ["id4", "employee_name_4", 0, 0, 0],
            ["id5", "employee_name_5", 0, 0, 0],
        ]
    }
    html_out = template.render(template_vars)
    HTML(string=html_out, base_url=f".").write_pdf("EmployeeTimesheetReport.pdf", stylesheets=["styles.css", CSS("https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css")])


def create_student_care_report():
    template = env.get_template('childcare_report_template.html')
    template_vars = {
        "title": "Student Care Service Report",
        "pca_logo": "pcalogo.svg",
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
