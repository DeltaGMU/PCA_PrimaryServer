from src.lib import global_vars
from src.lib.utils.session_manager import SessionManager, WebSessionManager
from src.lib.error_codes import ERR_SESSION_MNGR_NOT_INITIALIZED, ERR_WEB_SESSION_MNGR_NOT_INITIALIZED


class CoreService:
    def __init__(self, session_manager: SessionManager, web_session_manager: WebSessionManager):
        global_vars.session_manager = session_manager
        if not global_vars.session_manager:
            raise RuntimeError(f"Session Manager Error [Error Code: {ERR_SESSION_MNGR_NOT_INITIALIZED}]\n"
                               "The session manager was not initialized or encountered an error while initializing!\n"
                               "If you are the server administrator, please refer to the software manual!")
        global_vars.web_manager = web_session_manager
        if not global_vars.web_manager:
            raise RuntimeError(f"Web Session Manager Error [Error Code: {ERR_WEB_SESSION_MNGR_NOT_INITIALIZED}]\n"
                               "The web session manager was not initialized or encountered an error while initializing!\n"
                               "If you are the server administrator, please refer to the software manual!")
