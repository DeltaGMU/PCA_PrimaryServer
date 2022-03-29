from typing import Optional


class DefaultData:
    default_admin = {
        'employee_id': 'admin',
        'first_name': 'pca',
        'last_name': 'administrator',
        'plain_password': 'admin123',
        'primary_email': "admin@admin.com",
        'enable_primary_email_notifications': False,
        'role': 'administrator'
    }


class ThirdPartyRoutes:
    class Email:
        login = '/auth/authenticate-user'
        send_email = '/mail/message-put'


class APIRoutes:
    index = '/'
    core = '/api/v1'
    status = '/api/v1/status'
    routes = '/api/v1/routes'
    me = '/api/v1/me'
    login = '/api/v1/login'
    logout = '/api/v1/logout'
    register = '/api/v1/register'
    reset = '/api/v1/reset'
    forgot_password = '/api/v1/forgot_password'

    class Email:
        send_test_email = '/api/v1/email/test'

    class Reports:
        reports = '/api/v1/reports'
        employee_reports = '/api/v1/reports/employees'
        student_reports = '/api/v1/reports/students'
        timesheet_reports = '/api/v1/reports/timesheet'
        care_reports = '/api/v1/reports/care'

    class Employees:
        count = '/api/v1/employees/count'
        all_employees = '/api/v1/employees/all'
        one_employee = '/api/v1/employees/{employee_id}'
        employees = '/api/v1/employees'
        password = '/api/v1/employees/password/new'
        employee_token = '/api/v1/employees/token'

    class Students:
        count = '/api/v1/students/count'
        students = '/api/v1/students'
        one_student = '/api/v1/students/{student_id}'

    class StudentGrade:
        count = '/api/v1/grades/count'
        grades = '/api/v1/grades'
        one_grade = '/api/v1/grades/{grade_name}'

    class StudentCare:
        count = '/api/v1/care/count'
        care = '/api/v1/care'
        check_in = '/api/v1/care/checkin'
        check_out = '/api/v1/care/checkout'

    class StudentCareKiosk:
        one_student_info = '/api/v1/kiosk/info/{student_id}'
        one_student_care = '/api/v1/kiosk/care/{student_id}'

    class Timesheet:
        count = '/api/v1/timesheet/count'
        timesheet = '/api/v1/timesheet'
        one_timesheet = '/api/v1/timesheet/{employee_id}'
        hours_only = '/api/v1/timesheet/hours/{employee_id}'


API_ROUTES: APIRoutes = APIRoutes()
THIRD_PARTY_ROUTES: ThirdPartyRoutes = ThirdPartyRoutes()
