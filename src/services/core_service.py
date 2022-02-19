from src.lib.global_vars import SharedData
from src.lib.error_codes import ERR_SESSION_MNGR_NOT_INITIALIZED, ERR_WEB_SESSION_MNGR_NOT_INITIALIZED


class CoreService:
    def __init__(self):
        shared_data: SharedData = SharedData()
        if shared_data.Managers.get_session_manager() is None:
            raise RuntimeError(f"Session Manager Error [Error Code: {ERR_SESSION_MNGR_NOT_INITIALIZED}]\n"
                               "The session manager was not initialized or encountered an error while initializing!\n"
                               "If you are the server administrator, please refer to the software manual!")
        if shared_data.Managers.get_web_manager() is None:
            raise RuntimeError(f"Web Session Manager Error [Error Code: {ERR_WEB_SESSION_MNGR_NOT_INITIALIZED}]\n"
                               "The web session manager was not initialized or encountered an error while initializing!\n"
                               "If you are the server administrator, please refer to the software manual!")
