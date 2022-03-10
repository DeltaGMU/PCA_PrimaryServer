from pydantic import BaseSettings
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class APIRoutes:
    index = '/'
    core = '/api/v1'
    status = '/api/v1/status'
    me = '/api/v1/me'
    login = '/api/v1/login'
    logout = '/api/v1/logout'
    register = '/api/v1/register'

    class Employees:
        count = '/api/v1/employees/count'
        all_employees = '/api/v1/employees/all'
        one_employee = '/api/v1/employees/{employee_id}'
        employees = '/api/v1/employees'
        employee_token = '/api/v1/employees/token'

    class Students:
        count = '/api/v1/students/count'
        students = '/api/v1/students'
        student = '/api/v1/students/{student_id}'

    class StudentCare:
        count = 'api/v1/care/count'
        care = 'api/v1/care'
        check_in = 'api/v1/care/checkin'
        check_out = 'api/v1/care/checkout'
        report = 'api/v1/care/report'

    class Timesheet:
        count = 'api/v1/timesheet/count'
        timesheet = 'api/v1/timesheet'
        report = 'api/v1/timesheet/report'


class Settings(BaseSettings):
    API_ROUTES: APIRoutes = APIRoutes()
    mariadb_user: str
    mariadb_pass: str
    mariadb_host: str
    mariadb_port: int
    mariadb_database: str
    web_host: str
    web_port: int
    server_secret: str
    sys_debug_mode: Optional[bool] = False
    api_debug_mode: Optional[bool] = False
    db_debug_mode: Optional[bool] = False
    quiet_mode: Optional[bool] = False
    enable_logs: Optional[bool] = True
    log_level: Optional[str] = 'info'
    max_logs: Optional[int] = 10
    max_log_size: Optional[int] = 10485760
    log_directory: Optional[str] = None

    class Config:
        env_file = f'.env'
        env_file_encoding = 'utf-8'


load_dotenv()
ENV_SETTINGS = Settings()
