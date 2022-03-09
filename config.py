from pydantic import BaseSettings
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class APIRoutes:
    index = '/'
    core = '/api/v1/'
    status = '/api/v1/status'
    me = '/api/v1/me'
    login = '/api/v1/login'
    logout = '/api/v1/logout'
    register = '/api/v1/register'

    class Employees:
        count = '/api/v1/employees/count'
        employees = '/api/v1/employees'
        employee = '/api/v1/employees/{employee_id}'
        employee_token = '/api/v1/employees/token'


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
    debug_mode: Optional[bool] = False
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
