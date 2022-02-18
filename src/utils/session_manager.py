from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.lib.error_codes import ERR_SESSION_MNGR_INCORRECT_PARAMS
from fastapi.security import OAuth2PasswordBearer
from src.services.web_service import WebService


class SessionManager:
    def __init__(self,
                 server_host: str = None,
                 server_port: str = None,
                 server_db: str = None,
                 server_user: str = None,
                 server_pass: str = None,
                 debug_mode: bool = False):
        if None in (server_host, server_port, server_db, server_user, server_pass):
            raise RuntimeError(f"Session Manager Error [Error Code: {ERR_SESSION_MNGR_INCORRECT_PARAMS}]\n"
                               "One or more parameters required to start the service was null!\n"
                               "Please check your .env file or include the missing parameters as startup arguments.\n "
                               "If you are a server administrator, please refer to the software manual!")
        self.db_engine = create_engine(
            f"mariadb+mariadbconnector://{server_user}:{server_pass}@{server_host}:{server_port}/{server_db}",
            echo=debug_mode)
        self.session_factory = sessionmaker(bind=self.db_engine, autoflush=False, autocommit=False)
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

    def make_session(self):
        return self.session_factory()

    def get_engine(self):
        return self.db_engine


class WebSessionManager:
    web_service: WebService

    def __init__(self, *args, **kwargs):
        super(WebSessionManager, self).__init__(*args, **kwargs)
