from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.lib.error_codes import ERR_SESSION_MNGR_INCORRECT_PARAMS, ERR_WEB_SESSION_MNGR_INCORRECT_PARAMS
from src.lib.logging_manager import LoggingManager
from src.lib.strings import LOG_ORIGIN_STARTUP
from src.services.web_service import WebService
from src.lib.service_manager import SharedData


class DatabaseManager:
    def __init__(self,
                 server_host: str,
                 server_port: str,
                 server_db: str,
                 server_user: str,
                 server_pass: str):
        if None in (server_host, server_port, server_db, server_user, server_pass):
            raise RuntimeError(f"Session Manager Error [Error Code: {ERR_SESSION_MNGR_INCORRECT_PARAMS}]\n"
                               "One or more parameters provided to start the service was null!\n"
                               "Please check your .env file or include the missing parameters as startup arguments.\n "
                               "If you are a server administrator, please refer to the software manual!")
        self.db_engine = create_engine(
            f"mariadb+mariadbconnector://{server_user}:{server_pass}@{server_host}:{server_port}/{server_db}",
            echo=SharedData().Settings.get_debug_mode())
        self.session_factory = sessionmaker(bind=self.db_engine, autoflush=False, autocommit=False)
        LoggingManager().log(LoggingManager.LogLevel.LOG_CRITICAL, "Database manager initialized.", origin=LOG_ORIGIN_STARTUP, no_print=False)

    def make_session(self):
        return self.session_factory()

    def get_engine(self):
        return self.db_engine

    def is_active(self) -> bool:
        return self.db_engine is not None


class WebSessionManager:
    def __init__(self, web_ip: str, web_port: int):
        if None in (web_ip, web_port):
            raise RuntimeError(f"Web Session Manager Error [Error Code: {ERR_WEB_SESSION_MNGR_INCORRECT_PARAMS}]\n"
                               "One or more parameters provided to start the service was null!\n"
                               "Please check your .env file or include the missing parameters as startup arguments.\n "
                               "If you are a server administrator, please refer to the software manual!")
        # TODO: Add https/ssl certs into the service later.
        self.web_service: WebService = WebService(web_ip, web_port)
        LoggingManager().log(LoggingManager.LogLevel.LOG_CRITICAL, "Web session manager initialized.", origin=LOG_ORIGIN_STARTUP, no_print=False)

    def start_web_server(self):
        if self.web_service:
            self.web_service.initialize_web()

    def stop_web_server(self):
        if self.web_service:
            self.web_service.stop_web()
