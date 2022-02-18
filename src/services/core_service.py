from src.lib import global_vars
from src.utils.session_manager import SessionManager
from src.lib.error_codes import ERR_SESSION_MNGR_NOT_INITIALIZED


class CoreService:
    def __init__(self, session_manager: SessionManager):
        global_vars.session_manager = session_manager
        if not global_vars.session_manager:
            raise RuntimeError(f"Session Manager Error [Error Code: {ERR_SESSION_MNGR_NOT_INITIALIZED}]\n"
                               "The session manager was not initialized or encountered an error while initializing!\n"
                               "If you are the server administrator, please refer to the software manual!")



